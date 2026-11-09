"""Проверки вычислений и интерфейса командной строки."""

import json
import subprocess
import sys

import pytest

from practice2.physics import simulate

CASES = (
    (20, 0, 1, 15.095, -9.81, "airborne"),
    (0, 10, 1, 5.095, 0.19, "airborne"),
    (10, 0, 3, 0, 0, "landed"),
    (5, -2, 0.5, 2.77375, -6.905, "airborne"),
)


@pytest.mark.parametrize("height,velocity,time,y,speed,state", CASES)
def test_ballistic_cases(height, velocity, time, y, speed, state):
    """Четыре независимо рассчитанных примера движения."""
    payload = {
        "time": time,
        "gravity": 9.81,
        "balls": [{"height": height, "velocity": velocity}],
    }
    ball = simulate(payload)["balls"][0]
    assert ball["height"] == pytest.approx(y)
    assert ball["velocity"] == pytest.approx(speed)
    assert ball["state"] == state


@pytest.mark.parametrize("bad", [-1, True, "1", float("inf")])
def test_invalid_time(bad):
    """Некорректные физические параметры отклоняются."""
    with pytest.raises(ValueError):
        simulate({"time": bad, "balls": [{"height": 1}]})


def test_cli_reads_file(tmp_path):
    """CLI читает файл, а JSON-результат отправляет в stdout."""
    source = tmp_path / "input.json"
    source.write_text('{"time": 3, "balls": [{"height": 10}]}')
    result = subprocess.run(
        [sys.executable, "-m", "practice2.cli", str(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["balls"][0]["state"] == "landed"
    assert result.stderr == ""


def test_cli_invalid_file(tmp_path):
    """Ошибки файла идут в stderr и дают ненулевой exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "practice2.cli", str(tmp_path / "missing")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode
    assert not result.stdout
    assert result.stderr
