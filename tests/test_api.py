"""Интеграционные проверки настоящего HTTP и сохранения данных."""

import json
import threading
import time
from contextlib import contextmanager

import pytest

from practice2.client import ApiClient, ApiError
from practice2.model import Model
from practice2.server import make_server
from practice2.storage import FileStorage

ZERO = 0
NOW = 2000
OK = 200
NOT_ACCEPTABLE = 406


@contextmanager
def running_api(path, test_mode=True):
    """Поднять HTTP-сервер на свободном порту и закрыть после теста."""
    store = FileStorage(path)
    model = Model(store, test_mode=test_mode, clock=lambda: NOW)
    server = make_server(model, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = ApiClient("http://127.0.0.1:{}".format(server.server_port))
    try:
        yield client
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        model.close()
        store.close()


def test_nine_routes_and_restart(tmp_path):
    """Создать записи через HTTP и прочитать после перезапуска."""
    path = tmp_path / "db.json"
    with running_api(path) as client:
        member = client.save_member(1, {"ip": "127.0.0.1", "locale": "ru"})
        task = client.save_task(1, {"member": 1, "input": "{}", "tags": "a"})
        assert client.collect_member() == [member]
        assert client.read_member(1) == member
        assert client.collect_task(1) == [task]
        assert client.read_task(1) == task
        response = client.read_response(1)
        assert client.collect_response(1) == [response]
        assert response["status"] == "test"
        assert client.collect_report() == [["127.0.0.1", 0, "a"]]
    with running_api(path) as client:
        expected = [member, task, response]
        actual = [
            client.read_member(1),
            client.read_task(1),
            client.read_response(1),
        ]
        assert actual == expected


@pytest.mark.parametrize("headers", [{}, {"Accept": "text/json"}])
def test_required_headers(tmp_path, headers):
    """Каждый обязательный заголовок проверяется до маршрутизации."""
    with running_api(tmp_path / "db.json") as client:
        with pytest.raises(ApiError) as caught:
            client.request("POST", "/api/collect/report", headers=headers)
        assert caught.value.status == NOT_ACCEPTABLE


def test_real_subprocess(tmp_path):
    """EAN-13 создаётся в фоне отдельным процессом без shell."""
    payload = {"ean13": "590123412345"}
    with running_api(tmp_path / "db.json", test_mode=False) as client:
        client.save_member(1, {"ip": "::1", "locale": "ru"})
        client.save_task(1, {"member": 1, "input": json.dumps(payload)})
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            response = client.read_response(1)
            if response["status"] != "pending":
                break
            time.sleep(0.01)
        assert response["status"] == "success"
        assert "<svg" in response["response"]
        assert "5901234123457" in response["response"]
