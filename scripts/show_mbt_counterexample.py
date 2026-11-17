"""Показать контрпример MBT для одной ошибки в отдельной копии."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FAULT = (
    'return self.request("PUT", f"/api/save/task/{uid}", '
    '{key: value for key, value in values.items() if key != "tags"})'
)
ORIGINAL = 'return self.request("PUT", f"/api/save/task/{uid}", values)'


def main():
    """Испортить только временную копию и запустить модельный тест."""
    project = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="practice2-mbt-fault-") as name:
        workspace = Path(name)
        for folder in ("src", "tests"):
            shutil.copytree(project / folder, workspace / folder)
        client = workspace / "src" / "practice2" / "client.py"
        content = client.read_text(encoding="utf-8")
        if content.count(ORIGINAL) != 1:
            print("Не найдена ожидаемая строка HTTP-клиента", file=sys.stderr)
            return 1
        client.write_text(content.replace(ORIGINAL, FAULT), encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(workspace / "src"), str(workspace / "tests"))
        )
        print("Временная ошибка: ApiClient.save_task теряет поле tags.")
        print("Чистый проект не изменяется. Ожидается контрпример MBT.")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_mbt_file.py",
                "-q",
                "--tb=short",
            ],
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        if result.returncode and "Failing test case" in result.stdout:
            print("PASS: MBT нашёл ошибку только во временной копии.")
            return 0
        print("Контрпример не найден", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
