from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy.orm import Session

from db.models import Question
from db.session import DB_PATH, get_session, init_db

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json_questions(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def seed_from_json(session: Session, path: Path) -> int:
    questions = load_json_questions(path)
    count = 0
    for item in questions:
        existing = (
            session.query(Question)
            .filter(Question.year == item["year"], Question.question_no == item["question_no"])
            .one_or_none()
        )
        if existing:
            for key, value in item.items():
                setattr(existing, key, value)
        else:
            session.add(Question(**item))
            count += 1
    return count


def main() -> None:
    init_db()
    with get_session() as session:
        json_path = DATA_DIR / "sample_questions.json"
        if json_path.exists():
            inserted = seed_from_json(session, json_path)
            print(f"Seeded {inserted} records from {json_path.name}")
        else:
            print("No seed data found")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    main()
