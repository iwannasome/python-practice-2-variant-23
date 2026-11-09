"""Документное хранилище этапа 3 на библиотеке TinyDB."""

from copy import deepcopy
from pathlib import Path

from tinydb import Query, TinyDB


class TinyStorage:
    """Предоставлять тот же интерфейс хранилища для общей модели."""

    def __init__(self, path):
        """Открыть JSONStorage TinyDB и создать каталог."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.database = TinyDB(path, ensure_ascii=True, allow_nan=False)

    def all(self, entity):
        """Вернуть копии документов как обычные словари."""
        return [deepcopy(dict(row)) for row in self.database.table(entity)]

    def write(self, entity, row):
        """Вставить либо обновить документ по прикладному ключу uid."""
        self.database.table(entity).upsert(
            deepcopy(row), Query().uid == row["uid"]
        )

    def close(self):
        """Закрыть TinyDB и её файловый адаптер."""
        self.database.close()
