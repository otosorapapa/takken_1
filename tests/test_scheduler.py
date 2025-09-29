from logic.scheduler import score_priority


def test_scheduler_priority_bounds():
    priority = score_priority(0.9, 0, 1)
    assert 0 <= priority <= 1


def test_scheduler_overdue_boost():
    low = score_priority(0.5, 0, 3)
    high = score_priority(0.5, 60, 3)
    assert high > low


def test_scheduler_difficulty_boost():
    easy = score_priority(0.5, 0, 1)
    hard = score_priority(0.5, 0, 5)
    assert hard > easy
