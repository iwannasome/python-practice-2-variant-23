"""Выполнение CLI в отдельном процессе без командной оболочки."""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

TIMEOUT_SECONDS = 10
NANOSECONDS_PER_MILLISECOND = 1_000_000
ZERO = 0


def execute(content, test_mode=False):
    """Вернуть результат запуска или отметку тестового режима."""
    if test_mode:
        return {
            "response": '{"test_mode": true}',
            "status": "test",
            "failure": "",
            "duration": ZERO,
        }
    started = time.monotonic_ns()
    with tempfile.TemporaryDirectory(prefix="practice2-") as directory:
        source = Path(directory) / "input.json"
        source.write_text(content, encoding="utf-8")
        result = run_process(source)
    elapsed = time.monotonic_ns() - started
    result["duration"] = elapsed // NANOSECONDS_PER_MILLISECOND
    return result


def run_process(source):
    """Запустить ограниченный по времени процесс и сохранить ошибки."""
    try:
        process = subprocess.run(
            [sys.executable, "-m", "practice2.cli", str(source)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"response": "", "status": "error", "failure": str(error)}
    return {
        "response": process.stdout.strip(),
        "status": "error" if process.returncode else "success",
        "failure": process.stderr.strip(),
    }
