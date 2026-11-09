"""Независимая эталонная модель и генерируемые HTTP-сценарии."""

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
)
from support import ApiSession

from practice2.client import ApiError

TEXT = st.text(st.characters(exclude_categories=("Cs",)), max_size=12)
WINDOW = 540
FIRST = 1
ZERO = 0
NOT_FOUND = 404
CONFLICT = 409
BAD_REQUEST = 400
NOT_ACCEPTABLE = 406
METHOD_NOT_ALLOWED = 405


class ApiMachine(RuleBasedStateMachine):
    """Сравнивать HTTP API с независимыми словарями после действий."""

    session_class = ApiSession

    def __init__(self):
        """Начать новый сценарий с пустого дискового хранилища."""
        super().__init__()
        self.session = self.session_class()
        self.members = {}
        self.tasks = {}
        self.responses = {}

    @property
    def client(self):
        """Получить актуальный клиент, включая перезапуск сервера."""
        return self.session.client

    @initialize(ip=TEXT, tags=TEXT)
    def seed(self, ip, tags):
        """Начать с генерируемых данных и двух одинаковых проекций."""
        self.add_member(ip=ip)
        self.add_task(tags=tags)
        self.add_task(tags=tags)
        self.check_state()
        self.check_headers(headers={})
        self.check_headers(headers={"Accept": "text/json"})
        self.duplicate()
        self.missing()
        self.bad_query()
        self.filters()
        self.routing()
        self.advance_clock(WINDOW - FIRST)
        self.check_state()
        self.advance_clock(FIRST)
        self.check_state()
        self.session.now -= WINDOW + FIRST
        self.check_state()

    @rule(ip=TEXT)
    def add_member(self, ip):
        """Независимо построить ожидаемую запись Member."""
        uid = len(self.members) + FIRST
        expected = {
            "uid": uid,
            "datetime": self.session.now,
            "ip": ip,
            "locale": "ru",
        }
        assert self.client.save_member(uid, {"ip": ip}) == expected
        self.members[uid] = expected

    @rule(tags=TEXT)
    def add_task(self, tags):
        """Проверить Task и связанный Response тестового режима."""
        uid = len(self.tasks) + FIRST
        now = self.session.now
        values = {"member": FIRST, "input": "{}", "tags": tags}
        expected = dict(
            values,
            uid=uid,
            datetime=now,
            launched=now,
            completed=now,
        )
        assert self.client.save_task(uid, values) == expected
        self.tasks[uid] = expected
        self.responses[uid] = {
            "uid": uid,
            "datetime": now,
            "task": uid,
            "duration": ZERO,
            "status": "test",
            "failure": "",
            "response": '{"test_mode": true}',
        }

    @rule(delta=st.sampled_from([ZERO, FIRST, WINDOW - FIRST, WINDOW]))
    def advance_clock(self, delta):
        """Проверить строгое исключение границы девяти минут."""
        self.session.now += delta

    @rule()
    def restart(self):
        """Заново открыть БД и повторить HTTP-проверки."""
        self.session.restart()

    @rule()
    def duplicate(self):
        """Дубликаты сохраняют исходные записи."""
        with pytest.raises(ApiError) as caught:
            self.client.save_member(FIRST, {"ip": "duplicate"})
        assert caught.value.status == CONFLICT
        with pytest.raises(ApiError) as caught:
            self.client.save_task(FIRST, {"member": FIRST, "input": "{}"})
        assert caught.value.status == CONFLICT

    @rule()
    def missing(self):
        """Отклонить отсутствующие ключи и внешние ссылки."""
        absent = len(self.tasks) + len(self.members) + FIRST
        for read in (
            self.client.read_member,
            self.client.read_task,
            self.client.read_response,
        ):
            with pytest.raises(ApiError) as caught:
                read(absent)
            assert caught.value.status == NOT_FOUND
        with pytest.raises(ApiError) as caught:
            self.client.save_task(absent, {"member": absent, "input": "{}"})
        assert caught.value.status == NOT_FOUND

    @rule(
        headers=st.sampled_from(
            [
                {},
                {"Accept": "text/json"},
                {"Accept": "wrong", "Accept-Language": "ru"},
                {"Accept": "text/json", "Accept-Language": "en"},
            ]
        )
    )
    def check_headers(self, headers):
        """Оба заголовка обязательны, ошибка первого имеет приоритет."""
        with pytest.raises(ApiError) as caught:
            self.client.request("POST", "/api/collect/report", headers=headers)
        assert caught.value.status == NOT_ACCEPTABLE
        first = (
            "Accept"
            if headers.get("Accept") != "text/json"
            else "Accept-Language"
        )
        assert caught.value.payload["error"].startswith(f"Требуется {first}:")

    @rule()
    def bad_query(self):
        """Проверить неизвестные, повторные и некорректные параметры."""
        paths = [
            "/api/read/member",
            "/api/read/member?uid=bad",
            "/api/read/member?uid=0",
            "/api/read/member?uid=1&uid=2",
            "/api/read/member?unknown=x",
            "/api/read/member?uid=1&ip=x",
        ]
        for path in paths:
            with pytest.raises(ApiError) as caught:
                self.client.request("GET", path)
            assert caught.value.status == BAD_REQUEST

    @rule()
    def filters(self):
        """Проверить совпадение и отсутствие совпадения по полям."""
        ip = self.members[FIRST]["ip"]
        expected = [r for r in self.members.values() if r["ip"] == ip]
        assert self.client.collect_member({"ip": ip}) == expected
        assert self.client.collect_response(FIRST, {"status": "error"}) == []
        tag = self.tasks[FIRST]["tags"]
        expected = [r for r in self.tasks.values() if r["tags"] == tag]
        assert self.client.collect_task(FIRST, {"tags": tag}) == expected

    @rule()
    def routing(self):
        """Проверить неизвестный путь и метод существующего маршрута."""
        cases = [
            ("/missing", NOT_FOUND),
            ("/api/read/member", METHOD_NOT_ALLOWED),
        ]
        with pytest.raises(ApiError) as caught:
            self.client.request("DELETE", "/api/read/member")
        assert caught.value.status == METHOD_NOT_ALLOWED
        for path, status in cases:
            with pytest.raises(ApiError) as caught:
                self.client.request("POST", path)
            assert caught.value.status == status

    @invariant()
    def check_state(self):
        """Сопоставить девять API-операций с эталоном."""
        assert self.client.collect_member() == list(self.members.values())
        for uid, member in self.members.items():
            assert self.client.read_member(uid) == member
            expected = [r for r in self.tasks.values() if r["member"] == uid]
            assert self.client.collect_task(uid) == expected
        for uid, task in self.tasks.items():
            assert self.client.read_task(uid) == task
            expected = [self.responses[uid]]
            assert self.client.collect_response(uid) == expected
            assert self.client.read_response(uid) == self.responses[uid]
        assert self.client.collect_report() == self.expected_report()

    def expected_report(self):
        """Прямое тройное соединение без функций промышленной модели."""
        rows = {
            (member["ip"], response["duration"], task["tags"])
            for member in self.members.values()
            for task in self.tasks.values()
            for response in self.responses.values()
            if member["uid"] == task["member"]
            and task["uid"] == response["task"]
            and response["datetime"] > self.session.now - WINDOW
        }
        return [list(row) for row in sorted(rows)]

    def teardown(self):
        """Закрыть реальные HTTP-соединения и удалить временную БД."""
        self.session.close()


MBT_SETTINGS = settings(
    max_examples=25,
    stateful_step_count=25,
    deadline=None,
    derandomize=True,
)
