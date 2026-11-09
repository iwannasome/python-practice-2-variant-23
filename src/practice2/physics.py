"""Баллистика шариков до первого касания пола."""

import math

ZERO = 0
DEFAULT_GRAVITY = 9.81
MIN_BALLS = 1


def number(value, name, minimum=None):
    """Проверить конечное число; bool не является параметром модели."""
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name}: требуется конечное число")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name}: значение меньше {minimum}")
    return value


def ball_at_time(ball, elapsed, gravity):
    """Найти координату, скорость и время первого касания пола."""
    if not isinstance(ball, dict):
        raise ValueError("Шарик должен быть объектом JSON")
    height = number(ball.get("height"), "height", ZERO)
    velocity = number(ball.get("velocity", ZERO), "velocity")
    impact = velocity + math.sqrt(velocity**2 + 2 * gravity * height)
    impact /= gravity
    if elapsed >= impact:
        return {
            "height": ZERO,
            "velocity": ZERO,
            "impact_time": round(impact, 8),
            "state": "landed",
        }
    return {
        "height": round(
            height + velocity * elapsed - gravity * elapsed**2 / 2, 8
        ),
        "velocity": round(velocity - gravity * elapsed, 8),
        "impact_time": round(impact, 8),
        "state": "airborne",
    }


def simulate(payload):
    """Применить баллистику к списку шариков в момент time секунд."""
    if not isinstance(payload, dict):
        raise ValueError("Вход должен быть объектом JSON")
    elapsed = number(payload.get("time"), "time", ZERO)
    gravity = number(payload.get("gravity", DEFAULT_GRAVITY), "gravity")
    if gravity <= ZERO:
        raise ValueError("gravity должна быть положительной")
    balls = payload.get("balls")
    if not isinstance(balls, list) or len(balls) < MIN_BALLS:
        raise ValueError("balls должен быть непустым списком")
    return {
        "time": elapsed,
        "gravity": gravity,
        "balls": [ball_at_time(ball, elapsed, gravity) for ball in balls],
    }
