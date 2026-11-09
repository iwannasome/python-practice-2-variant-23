"""Жизненный цикл настоящего HTTP-сервера для модельных тестов."""

import threading
from tempfile import TemporaryDirectory

from practice2.client import ApiClient
from practice2.model import Model
from practice2.server import make_server
from practice2.storage import FileStorage

FIXED_TIME = 2000


class ApiSession:
    """Создавать отдельную БД и HTTP-сервер для каждого сценария."""

    storage_class = FileStorage

    def __init__(self):
        """Открыть временную БД и включить управляемые тестовые часы."""
        self.directory = TemporaryDirectory(prefix="mbt-practice2-")
        self.path = self.directory.name + "/database.json"
        self.now = FIXED_TIME
        self.start()

    def start(self):
        """Открыть хранилище и HTTP-сервер на свободном порту."""
        self.storage = self.storage_class(self.path)
        model = Model(self.storage, test_mode=True, clock=lambda: self.now)
        self.server = make_server(model, port=0)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        self.thread.start()
        self.client = ApiClient(f"http://127.0.0.1:{self.server.server_port}")

    def stop(self):
        """Дождаться остановки потока и закрыть хранилище."""
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.storage.close()

    def restart(self):
        """Проверять чтение с диска после полного закрытия хранилища."""
        self.stop()
        self.start()

    def close(self):
        """Удалить временные данные после завершения сценария."""
        self.stop()
        self.directory.cleanup()
