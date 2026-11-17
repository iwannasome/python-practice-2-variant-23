"""Выполнение CLI в отдельном процессе без командной оболочки."""

import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from practice2.schema import validate

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


class TaskScheduler:
    """Выполнять CLI в фоне после сохранения принятого задания."""

    def __init__(self, storage, lock, clock, test_mode):
        """Принять общее хранилище и замок модели."""
        self.storage = storage
        self.lock = lock
        self.clock = clock
        self.test_mode = test_mode
        self.pool = ThreadPoolExecutor(max_workers=2)

    def prepare(self, row):
        """Создать тестовый или ожидающий Response для нового Task."""
        if self.test_mode:
            row["completed"] = int(self.clock())
            result = execute("", test_mode=True)
        else:
            result = {
                "response": "",
                "status": "pending",
                "failure": "",
                "duration": ZERO,
            }
        return dict(
            result, uid=row["uid"], task=row["uid"], datetime=int(self.clock())
        )

    def start(self, uid, content):
        """Отправить обычное задание в пул после записи на диск."""
        if not self.test_mode:
            self.pool.submit(self._complete, uid, content)

    def _complete(self, uid, content):
        """Выполнить CLI и атомарно для API обновить Task и Response."""
        result = execute(content)
        with self.lock:
            task = next(
                row for row in self.storage.all("task") if row["uid"] == uid
            )
            task["completed"] = int(self.clock())
            response = dict(
                result, uid=uid, task=uid, datetime=task["completed"]
            )
            validate("response", response)
            self.storage.write("task", task)
            self.storage.write("response", response)

    def close(self):
        """Дождаться всех запущенных вычислений перед закрытием БД."""
        self.pool.shutdown(wait=True)
