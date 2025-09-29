from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Any

import pandas as pd

from db.models import Question
from db.session import get_session, init_db

logger = logging.getLogger(__name__)
LOG_PATH = Path("logs/app.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers):
    handler = logging.handlers.RotatingFileHandler(
        LOG_PATH, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def export_questions_to_csv(path: str, filters: dict[str, Any] | None = None) -> int:
    init_db()
    with get_session() as session:
        query = session.query(Question)

        if filters:
            if ids := filters.get("ids"):
                query = query.filter(Question.id.in_(ids))
            if categories := filters.get("categories"):
                query = query.filter(Question.category.in_(categories))
            if year_range := filters.get("year_range"):
                start, end = year_range
                query = query.filter(Question.year.between(start, end))
            if difficulty_range := filters.get("difficulty_range"):
                low, high = difficulty_range
                query = query.filter(Question.difficulty.between(low, high))
            if tags := filters.get("tags"):
                for tag in tags:
                    query = query.filter(Question.tags.contains(tag))

        records = query.all()

    if not records:
        pd.DataFrame().to_csv(path, index=False)
        logger.info("Exported 0 records to %s", path)
        return 0

    rows = []
    for q in records:
        rows.append(
            {
                "year": q.year,
                "question_no": q.question_no,
                "category": q.category,
                "difficulty": q.difficulty,
                "question_text": q.question_text,
                "choiceA": q.choices.get("A"),
                "choiceB": q.choices.get("B"),
                "choiceC": q.choices.get("C"),
                "choiceD": q.choices.get("D"),
                "correct": q.correct,
                "explanation": q.explanation,
                "law_references": q.law_references,
                "revised_year": q.revised_year,
                "tags": q.tags,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    logger.info("Exported %s records to %s", len(rows), path)
    return len(rows)
