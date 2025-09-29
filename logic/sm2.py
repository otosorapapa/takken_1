from __future__ import annotations

from typing import Tuple


def update_sm2(ef: float, interval: int, repetition: int, quality: int) -> tuple[float, int, int, int]:
    """Apply the SM-2 spaced repetition update rules.

    Args:
        ef: Current easiness factor.
        interval: Current review interval in days.
        repetition: Current repetition count.
        quality: Response quality (0-5 scale). In this app 4=correct, 2=incorrect.

    Returns:
        Tuple of (new_ef, new_interval, new_repetition, next_interval).
    """

    quality = max(0, min(5, quality))
    ef = max(1.3, ef)

    if quality < 3:
        new_repetition = 0
        new_interval = 1
        new_ef = ef
    else:
        if repetition == 0:
            new_interval = 1
        elif repetition == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(interval * ef))
        new_ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)
        new_repetition = repetition + 1

    return float(new_ef), int(new_interval), int(new_repetition), int(new_interval)
