"""Регрессионные проверки замечаний независимого ревью."""

import json
import subprocess
import sys
from http.client import HTTPConnection

import pytest
from test_api import NOT_ACCEPTABLE, running_api


@pytest.mark.parametrize("method", ["PATCH", "OPTIONS", "HEAD", "CUSTOM"])
def test_all_methods_require_headers(tmp_path, method):
    """Любой HTTP-метод сначала проверяет обязательные заголовки."""
    with running_api(tmp_path / "db.json") as client:
        host = client.base_url.removeprefix("http://")
        connection = HTTPConnection(host)
        try:
            connection.request(method, "/api/read/member?uid=1")
            response = connection.getresponse()
            assert response.status == NOT_ACCEPTABLE
            assert response.getheader("Content-Type").startswith(
                "application/json"
            )
            response.read()
        finally:
            connection.close()


def test_compute_rejects_infinite_result(tmp_path):
    """Команда compute не печатает невалидные Infinity и NaN."""
    source = tmp_path / "large.json"
    source.write_text(
        json.dumps(
            {
                "time": 0,
                "gravity": 1e308,
                "balls": [{"height": 1}],
            }
        )
    )
    process = subprocess.run(
        [sys.executable, "-m", "practice2", "compute", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode
    assert process.stdout == ""
    assert process.stderr
