import pandas as pd

from logic.sampling import TARGET_DISTRIBUTION, sample_mock


def test_sample_mock_distribution():
    rows = []
    id_counter = 1
    for category, count in TARGET_DISTRIBUTION.items():
        for _ in range(count * 2):
            rows.append({"id": id_counter, "category": category, "year": 2020, "difficulty": 3})
            id_counter += 1
    df = pd.DataFrame(rows)
    ids = sample_mock(df, seed=42)
    assert len(ids) == 50 or len(df) < 50
    assert len(ids) == len(set(ids))

    counts = df[df["id"].isin(ids)]["category"].value_counts()
    for category, expected in TARGET_DISTRIBUTION.items():
        if counts.get(category, 0) > 0:
            assert counts[category] <= expected or len(df) < 50
