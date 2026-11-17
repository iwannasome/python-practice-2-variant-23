"""Проверка неблокирующего запуска вычислительной задачи."""

import threading
import time

from test_api import NOW, running_api

NOT_COMPLETED = 0


def test_task_returns_while_worker_waits(tmp_path, monkeypatch):
    """HTTP PUT возвращается до завершения отдельного вычисления."""
    started = threading.Event()
    release = threading.Event()

    def blocked(_content):
        """Дождаться явного разрешения теста завершить работу."""
        started.set()
        assert release.wait(5)
        return {
            "response": "<svg/>",
            "status": "success",
            "failure": "",
            "duration": 1,
        }

    monkeypatch.setattr("practice2.runner.execute", blocked)
    with running_api(tmp_path / "db.json", test_mode=False) as client:
        client.timeout = 2
        client.save_member(1, {"ip": "127.0.0.1"})
        try:
            task = client.save_task(1, {"member": 1, "input": "{}"})
            assert task["completed"] == NOT_COMPLETED
            assert started.wait(2)
            assert client.read_response(1)["status"] == "pending"
        finally:
            release.set()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if client.read_response(1)["status"] == "success":
                break
            time.sleep(0.01)
        assert client.read_response(1)["response"] == "<svg/>"
        assert client.read_task(1)["completed"] == NOW
