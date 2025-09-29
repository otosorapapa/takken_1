from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from db.models import Question
from db.session import DB_PATH, engine, get_session, init_db


@pytest.fixture(autouse=True)
def clean_database(tmp_path):
    if os.path.exists(DB_PATH):
        engine.dispose()
        os.remove(DB_PATH)
    init_db()
    yield
    if os.path.exists(DB_PATH):
        engine.dispose()
        os.remove(DB_PATH)


@pytest.fixture
def sample_question_data():
    return {
        "year": 2024,
        "question_no": 1,
        "category": "宅建業法",
        "difficulty": 3,
        "question_text": "テスト問題",
        "choices": {"A": "1", "B": "2", "C": "3", "D": "4"},
        "correct": "A",
        "explanation": "テスト解説",
        "law_references": "テスト法",
        "revised_year": 2023,
        "tags": "テスト",
    }


@pytest.fixture
def insert_questions(sample_question_data):
    with get_session() as session:
        for idx in range(1, 5):
            data = sample_question_data.copy()
            data["question_no"] = idx
            data["choices"] = {"A": "1", "B": "2", "C": "3", "D": "4"}
            data["correct"] = "A"
            session.add(Question(**data))
    return True


@pytest.fixture
def sid() -> str:
    return "test-sid"
