"""Общая модель данных и девять операций HTTP API."""

import threading
import time

from practice2.runner import execute
from practice2.schema import (
    WINDOW_SECONDS,
    ConflictError,
    MissingError,
    defaults,
    uid_value,
    validate,
)


class Model:
    """Обеспечивать ключи, связи, вычисления и реляционный отчёт."""

    def __init__(self, storage, test_mode=False, clock=time.time):
        """Принять взаимозаменяемое хранилище и источник времени."""
        self.storage = storage
        self.test_mode = test_mode
        self.clock = clock
        self.lock = threading.RLock()

    def _read(self, entity, uid):
        """Получить одну запись, строго проверив ключ."""
        uid_value(uid)
        rows = [r for r in self.storage.all(entity) if r["uid"] == uid]
        if not rows:
            raise MissingError(f"{entity} {uid}: запись не найдена")
        return rows[0]

    def _collect(self, entity, filters):
        """Выбрать документы по точному совпадению заданных полей."""
        validate(entity, filters, partial=True)
        with self.lock:
            rows = self.storage.all(entity)
        return sorted(
            [r for r in rows if all(r[k] == v for k, v in filters.items())],
            key=lambda row: row["uid"],
        )

    def _new(self, entity, uid, values):
        """Проверить новую запись до изменения состояния."""
        row = defaults(entity, uid, values, self.clock)
        if any(r["uid"] == uid for r in self.storage.all(entity)):
            raise ConflictError(f"{entity} {uid}: ключ уже существует")
        return row

    def save_member(self, uid, values):
        """Создать Member с ключом из пути и полями из query."""
        with self.lock:
            row = self._new("member", uid, values)
            self.storage.write("member", row)
            return row

    def collect_member(self, filters=None):
        """Найти Member по полям; пустой фильтр выбирает всех."""
        return self._collect("member", filters or {})

    def read_member(self, uid):
        """Прочитать одного Member по uid."""
        with self.lock:
            return self._read("member", uid)

    def save_task(self, uid, values):
        """Создать Task, выполнить CLI и сохранить Response."""
        with self.lock:
            row = self._new("task", uid, values)
            self._read("member", row["member"])
            row["launched"] = int(self.clock())
            result = execute(row["input"], self.test_mode)
            row["completed"] = int(self.clock())
            response = dict(
                result, uid=uid, task=uid, datetime=row["completed"]
            )
            validate("response", response)
            self.storage.write("task", row)
            self.storage.write("response", response)
            return row

    def collect_task(self, member, filters=None):
        """Найти задания участника с дополнительными фильтрами."""
        uid_value(member)
        return self._collect("task", dict(filters or {}, member=member))

    def read_task(self, uid):
        """Прочитать одно задание по uid."""
        with self.lock:
            return self._read("task", uid)

    def collect_response(self, task, filters=None):
        """Найти ответы задания с дополнительными фильтрами."""
        uid_value(task)
        return self._collect("response", dict(filters or {}, task=task))

    def read_response(self, uid):
        """Прочитать один ответ по uid."""
        with self.lock:
            return self._read("response", uid)

    def collect_report(self):
        """Вычислить уникальные [ip, duration, tags] по формуле 23."""
        with self.lock:
            members = {r["uid"]: r for r in self.storage.all("member")}
            tasks = {r["uid"]: r for r in self.storage.all("task")}
            cutoff = self.clock() - WINDOW_SECONDS
            result = set()
            for response in self.storage.all("response"):
                if response["datetime"] <= cutoff:
                    continue
                task = tasks[response["task"]]
                member = members[task["member"]]
                result.add((member["ip"], response["duration"], task["tags"]))
            return [list(row) for row in sorted(result)]
