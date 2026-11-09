"""Тот же независимый MBT для документной версии этапа 3."""

from mbt_machine import MBT_SETTINGS, ApiMachine
from support import ApiSession

from practice2.tiny_storage import TinyStorage


class TinySession(ApiSession):
    """Заменить только адаптер хранилища, сохраняя HTTP-проверки."""

    storage_class = TinyStorage


class TinyMachine(ApiMachine):
    """Использовать неизменный эталон и правила с TinyDB."""

    session_class = TinySession


TestTinyApi = TinyMachine.TestCase
TestTinyApi.settings = MBT_SETTINGS
