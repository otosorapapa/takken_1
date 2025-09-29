from logic.sm2 import update_sm2


def test_sm2_correct_answer_increases_interval():
    ef, interval, repetition, _ = update_sm2(2.5, 1, 1, 4)
    assert interval >= 6
    assert repetition == 2
    assert ef >= 2.5


def test_sm2_incorrect_resets_repetition():
    ef, interval, repetition, _ = update_sm2(2.5, 10, 3, 2)
    assert repetition == 0
    assert interval == 1
    assert ef >= 1.3


def test_sm2_ef_floor():
    ef, _, _, _ = update_sm2(1.1, 1, 0, 2)
    assert ef == 1.3
