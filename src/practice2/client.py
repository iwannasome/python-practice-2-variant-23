"""HTTP-клиент с именами методов, совпадающими с моделью данных."""

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HEADERS = {"Accept": "text/json", "Accept-Language": "ru"}


class ApiError(ValueError):
    """Ответ HTTP API с кодом ошибки и JSON-сообщением."""

    def __init__(self, status, payload):
        """Сохранить код и тело ответа для программной обработки."""
        super().__init__(payload.get("error", str(payload)))
        self.status = status
        self.payload = payload


class ApiClient:
    """Управлять данными через настоящие HTTP-запросы."""

    def __init__(self, base_url="http://127.0.0.1:8024", timeout=15):
        """Настроить базовый URL и тайм-аут клиента в секундах."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method, path, params=None, headers=None):
        """Выполнить запрос с query-параметрами и прочитать JSON."""
        query = urlencode(params or {})
        url = self.base_url + path + (f"?{query}" if query else "")
        request = Request(
            url,
            method=method,
            headers=HEADERS if headers is None else headers,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except HTTPError as error:
            with error:
                body = error.read()
                payload = json.loads(body) if body else {"error": error.reason}
            raise ApiError(error.code, payload) from error

    def save_member(self, uid, values):
        """Создать Member по uid и полям."""
        return self.request("PUT", f"/api/save/member/{uid}", values)

    def collect_member(self, filters=None):
        """Выбрать участников по полям."""
        return self.request("POST", "/api/collect/member", filters)

    def read_member(self, uid):
        """Прочитать одного участника."""
        return self.request("GET", "/api/read/member", {"uid": uid})

    def save_task(self, uid, values):
        """Создать и синхронно выполнить задание."""
        return self.request("PUT", f"/api/save/task/{uid}", values)

    def collect_task(self, member, filters=None):
        """Выбрать задания участника."""
        return self.request("POST", f"/api/collect/task/{member}", filters)

    def read_task(self, uid):
        """Прочитать одно задание."""
        return self.request("GET", "/api/read/task", {"uid": uid})

    def collect_response(self, task, filters=None):
        """Выбрать ответы задания."""
        return self.request("POST", f"/api/collect/response/{task}", filters)

    def read_response(self, uid):
        """Прочитать один ответ."""
        return self.request("GET", "/api/read/response", {"uid": uid})

    def collect_report(self):
        """Получить уникальную проекцию за последние девять минут."""
        return self.request("POST", "/api/collect/report")
