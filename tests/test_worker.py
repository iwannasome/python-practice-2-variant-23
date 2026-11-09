"""Проверки subprocess и тестового режима."""

import subprocess

from practice2.runner import execute, run_process


def test_mode_does_not_start_process(monkeypatch):
    """Даже некорректный ввод в тестовом режиме не запускает CLI."""

    def forbidden(*args, **kwargs):
        """Немедленно выявить попытку запустить реальный процесс."""
        raise AssertionError("subprocess не должен запускаться")

    monkeypatch.setattr(subprocess, "run", forbidden)
    assert execute("not-json", test_mode=True)["status"] == "test"


def test_invalid_computation_is_recorded():
    """Ошибка CLI превращается в данные Response без падения сервера."""
    result = execute('{"time": -1, "balls": []}')
    assert result["status"] == "error"
    assert result["failure"]
    assert result["response"] == ""


def test_process_timeout(monkeypatch, tmp_path):
    """Тайм-аут дочернего процесса имеет явный статус ошибки."""

    def expired(*args, **kwargs):
        """Имитировать исключение стандартного subprocess.run."""
        raise subprocess.TimeoutExpired("practice2.cli", timeout=10)

    monkeypatch.setattr(subprocess, "run", expired)
    result = run_process(tmp_path / "input.json")
    assert result["status"] == "error"
    assert result["failure"]
