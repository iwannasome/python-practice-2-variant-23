"""Проверка покрытия всех маршрутов по отдельному MBT-отчёту."""

import json
import sys
from pathlib import Path

FULL_COVERAGE = 100
EXPECTED_OPERATIONS = {
    "save_member",
    "collect_member",
    "read_member",
    "save_task",
    "collect_task",
    "read_task",
    "collect_response",
    "read_response",
    "collect_report",
}


def check(path):
    """Потребовать branch coverage и полное покрытие HTTP и модели."""
    from practice2.routes import ROUTES

    report = json.loads(Path(path).read_text(encoding="utf-8"))
    assert report["meta"]["branch_coverage"], "Нужен запуск с --branch"
    assert {row[2] for row in ROUTES} == EXPECTED_OPERATIONS
    required = {"model.py", "routes.py", "server.py", "client.py"}
    for filename, details in report["files"].items():
        name = Path(filename).name
        if name in required:
            summary = details["summary"]
            assert summary["percent_covered"] == FULL_COVERAGE, filename
            print(f"PASS {name}: 100% строк и ветвей")
            required.remove(name)
    assert not required, f"Нет измерений для {required}"
    print("PASS: все 9 маршрутов покрыты отдельным запуском MBT")


if __name__ == "__main__":
    check(sys.argv[1])
