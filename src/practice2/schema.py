"""Поля ER-схемы и строгая проверка типов и ключей."""

import time

SCHEMAS = {
    "member": {"uid": int, "datetime": int, "ip": str, "locale": str},
    "task": {
        "uid": int,
        "datetime": int,
        "input": str,
        "member": int,
        "tags": str,
        "completed": int,
        "launched": int,
    },
    "response": {
        "uid": int,
        "datetime": int,
        "response": str,
        "status": str,
        "failure": str,
        "task": int,
        "duration": int,
    },
}
MIN_UID = 1
ZERO = 0
WINDOW_SECONDS = 9 * 60


class MissingError(ValueError):
    """Запись с заданным ключом отсутствует."""


class ConflictError(ValueError):
    """Первичный ключ уже занят."""


def uid_value(uid):
    """Принять только положительный целый первичный ключ."""
    if type(uid) is not int or uid < MIN_UID:
        raise ValueError("uid должен быть положительным целым")
    return uid


def validate(entity, values, partial=False):
    """Проверить имена полей, точные типы и ограничения ключей."""
    fields = SCHEMAS[entity]
    if not isinstance(values, dict) or not values.keys() <= fields.keys():
        raise ValueError(f"Неизвестные поля {entity}")
    if not partial and values.keys() != fields.keys():
        raise ValueError(f"Требуются все поля {entity}")
    for name, value in values.items():
        if type(value) is not fields[name]:
            raise ValueError(f"{name}: ожидается {fields[name].__name__}")
        if name in {"uid", "member", "task"}:
            uid_value(value)
    if entity == "response" and values.get("duration", ZERO) < ZERO:
        raise ValueError("duration должна быть неотрицательной")


def defaults(entity, uid, values, clock=time.time):
    """Сформировать запись, сохраняя пользовательские значения полей."""
    row = {"uid": uid, "datetime": int(clock())}
    if entity == "member":
        row.update(ip="", locale="ru")
    else:
        row.update(tags="", completed=ZERO, launched=ZERO)
    row.update(values)
    if row["uid"] != uid:
        raise ValueError("uid в пути и данных различаются")
    validate(entity, row)
    return row
