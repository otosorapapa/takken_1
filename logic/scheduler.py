from __future__ import annotations


def score_priority(
    correct_rate: float, overdue_days: int, difficulty: int, w: tuple[float, float, float] = (0.5, 0.3, 0.2)
) -> float:
    """Calculate scheduling priority for a question."""

    w1, w2, w3 = w
    correct_rate = min(max(correct_rate, 0.0), 1.0)
    overdue_ratio = max(0.0, overdue_days) / 30.0
    difficulty_norm = min(max(difficulty, 1), 5)
    difficulty_norm = (difficulty_norm - 1) / 4

    priority = w1 * (1.0 - correct_rate) + w2 * overdue_ratio + w3 * difficulty_norm
    return float(priority)
