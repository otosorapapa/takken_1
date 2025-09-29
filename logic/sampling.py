from __future__ import annotations

import random
from typing import Iterable

import pandas as pd

TARGET_DISTRIBUTION = {
    "宅建業法": 20,
    "権利関係": 14,
    "法令上の制限": 12,
    "税・その他": 4,
}
TOTAL_QUESTIONS = 50


def _pick(rng: random.Random, ids: Iterable[int], count: int) -> list[int]:
    pool = list(ids)
    if not pool:
        return []
    if len(pool) <= count:
        rng.shuffle(pool)
        return pool
    return rng.sample(pool, count)


def sample_mock(questions_df: pd.DataFrame, seed: int | None = None) -> list[int]:
    """Return a list of question IDs for the mock exam."""

    if "id" not in questions_df.columns:
        raise ValueError("questions_df must include an 'id' column")

    rng = random.Random(seed)
    selected: list[int] = []

    remaining_df = questions_df.copy()

    for category, target in TARGET_DISTRIBUTION.items():
        cat_ids = remaining_df.loc[remaining_df["category"] == category, "id"].tolist()
        picks = _pick(rng, cat_ids, target)
        selected.extend(picks)
        remaining_df = remaining_df[~remaining_df["id"].isin(selected)]

    if len(selected) < TOTAL_QUESTIONS:
        deficit = TOTAL_QUESTIONS - len(selected)
        remaining_ids = remaining_df["id"].tolist()
        selected.extend(_pick(rng, remaining_ids, deficit))

    return selected[:TOTAL_QUESTIONS]
