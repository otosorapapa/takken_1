from __future__ import annotations

import logging
import logging.handlers
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

from db.models import Question, CATEGORIES
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


class QuestionRow(BaseModel):
    year: int = Field(..., gt=1900, le=date.today().year)
    question_no: int = Field(..., ge=1, le=100)
    category: str
    difficulty: int = Field(..., ge=1, le=5)
    question_text: str
    choiceA: str
    choiceB: str
    choiceC: str
    choiceD: str
    correct: str
    explanation: str | None = None
    law_references: str | None = None
    revised_year: int | None = None
    tags: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"category must be one of {', '.join(CATEGORIES)}")
        return value

    @field_validator("correct")
    @classmethod
    def validate_correct(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in {"A", "B", "C", "D"}:
            raise ValueError("correct must be A-D")
        return value

    @field_validator("choiceA", "choiceB", "choiceC", "choiceD")
    @classmethod
    def validate_choice(cls, value: str) -> str:
        if not value or not str(value).strip():
            raise ValueError("choice text is required")
        return str(value)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        tags = [tag.strip() for tag in value.split(",") if tag.strip()]
        for tag in tags:
            if len(tag) > 32:
                raise ValueError("each tag must be <=32 characters")
        return ",".join(tags)

    def to_question_dict(self) -> dict[str, Any]:
        return {
            "year": self.year,
            "question_no": self.question_no,
            "category": self.category,
            "difficulty": self.difficulty,
            "question_text": self.question_text,
            "choices": {
                "A": self.choiceA,
                "B": self.choiceB,
                "C": self.choiceC,
                "D": self.choiceD,
            },
            "correct": self.correct,
            "explanation": self.explanation,
            "law_references": self.law_references,
            "revised_year": self.revised_year,
            "tags": self.tags,
        }


def validate_row(row: dict[str, Any]) -> tuple[bool, list[str]]:
    try:
        QuestionRow(**row)
        return True, []
    except ValidationError as exc:
        messages = []
        for error in exc.errors():
            loc = ".".join(str(item) for item in error["loc"])
            messages.append(f"{loc}: {error['msg']}")
        return False, messages


def import_questions_from_csv(path: str) -> tuple[int, int, list[dict[str, Any]]]:
    init_db()
    df = pd.read_csv(path, dtype=str).fillna("")

    inserted = 0
    skipped = 0
    errors: list[dict[str, Any]] = []

    with get_session() as session:
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            is_valid, messages = validate_row(row_dict)
            if not is_valid:
                skipped += 1
                error_entry = {"row": int(idx) + 2, "messages": messages}
                errors.append(error_entry)
                logger.error("Validation error at row %s: %s", idx + 2, messages)
                continue

            record = QuestionRow(**row_dict)
            data = record.to_question_dict()
            existing = (
                session.query(Question)
                .filter(Question.year == data["year"], Question.question_no == data["question_no"])
                .one_or_none()
            )
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                session.add(Question(**data))
                inserted += 1

    return inserted, skipped, errors
