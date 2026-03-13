from __future__ import annotations

import time


def sleep_seconds(seconds: int) -> None:
    time.sleep(seconds)


def poll_until(
    condition_func,
    interval_seconds: int,
    max_attempts: int,
) -> bool:
    """
    Ejecuta condition_func periódicamente hasta que retorne True
    o se alcancen los intentos máximos.
    """
    for _ in range(max_attempts):
        if condition_func():
            return True
        time.sleep(interval_seconds)

    return False