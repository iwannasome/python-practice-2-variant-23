"""Маршруты таблицы 23 и преобразование параметров query."""

import re
from urllib.parse import parse_qs, urlsplit

from practice2.schema import SCHEMAS

ROUTES = (
    ("PUT", r"/api/save/member/([^/]+)", "save_member", "member"),
    ("POST", r"/api/collect/member", "collect_member", "member"),
    ("GET", r"/api/read/member", "read_member", "member"),
    ("PUT", r"/api/save/task/([^/]+)", "save_task", "task"),
    ("POST", r"/api/collect/task/([^/]+)", "collect_task", "task"),
    ("GET", r"/api/read/task", "read_task", "task"),
    ("POST", r"/api/collect/response/([^/]+)", "collect_response", "response"),
    ("GET", r"/api/read/response", "read_response", "response"),
    ("POST", r"/api/collect/report", "collect_report", None),
)
ONE_VALUE = 1


class RouteError(ValueError):
    """Неизвестный маршрут или неподдерживаемый HTTP-метод."""

    def __init__(self, status, message):
        """Сохранить HTTP-статус ошибки маршрутизации."""
        super().__init__(message)
        self.status = status


def parse_values(entity, query):
    """Отклонить повторы и неизвестные поля, преобразовать целые."""
    raw = parse_qs(query, keep_blank_values=True, strict_parsing=True)
    schema = SCHEMAS.get(entity, {})
    values = {}
    for name, items in raw.items():
        if name not in schema or len(items) != ONE_VALUE:
            raise ValueError(f"Недопустимый параметр {name}")
        values[name] = schema[name](items[0])
    return values


def resolve(method, target):
    """Найти обработчик и проверить метод независимо от query."""
    url = urlsplit(target)
    for verb, pattern, operation, entity in ROUTES:
        match = re.fullmatch(pattern, url.path)
        if match is None:
            continue
        if method != verb:
            raise RouteError(405, "Метод не разрешён для маршрута")
        key = int(match.group(1)) if match.groups() else None
        return operation, entity, key, url.query
    raise RouteError(404, "Маршрут не найден")


def dispatch(model, method, target):
    """Передать типизированные аргументы соответствующему методу."""
    name, entity, key, query = resolve(method, target)
    values = parse_values(entity, query)
    operation = getattr(model, name)
    if name.startswith("read_"):
        if set(values) != {"uid"}:
            raise ValueError("Требуется только параметр uid")
        return operation(values["uid"])
    if name == "collect_report":
        return operation()
    if key is not None:
        return operation(key, values)
    return operation(values)
