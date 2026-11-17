"""Файловое хранилище этапа 2 с атомарной заменой JSON-файла."""

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

ENTITIES = ("member", "task", "response")


class FileStorage:
    """Хранить три таблицы на диске; один экземпляр на сервер."""

    def __init__(self, path):
        """Прочитать существующие данные или создать пустые таблицы."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tables = {name: {} for name in ENTITIES}
        if self.path.exists():
            self.tables = json.loads(self.path.read_text(encoding="utf-8"))

    def all(self, entity):
        """Вернуть независимые копии документов таблицы."""
        return deepcopy(list(self.tables[entity].values()))

    def write(self, entity, row):
        """Атомарно записать документ на диск."""
        updated = deepcopy(self.tables)
        updated[entity][str(row["uid"])] = deepcopy(row)
        handle, name = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(updated, stream, ensure_ascii=True, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
            self.tables = updated
        finally:
            Path(name).unlink(missing_ok=True)

    def close(self):
        """Не удерживать дескрипторы между вызовами."""
