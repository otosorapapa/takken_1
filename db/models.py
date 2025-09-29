from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

CATEGORIES = ["権利関係", "宅建業法", "法令上の制限", "税・その他"]


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    question_no = Column(Integer, nullable=False)
    category = Column(String(32), nullable=False, index=True)
    difficulty = Column(Integer, nullable=False, default=3)
    question_text = Column(Text, nullable=False)
    choices = Column(JSON, nullable=False)
    correct = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=True)
    law_references = Column(Text, nullable=True)
    revised_year = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)

    progresses = relationship("UserProgress", back_populates="question", cascade="all, delete")

    __table_args__ = (
        Index("ix_question_year_no", "year", "question_no", unique=True),
    )


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(String(64), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_bookmarked = Column(Boolean, nullable=False, default=False)
    is_marked_for_review = Column(Boolean, nullable=False, default=False)
    last_answer = Column(String(1), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    answer_time_sec = Column(Integer, nullable=True)
    ef = Column(Float, nullable=False, default=2.5)
    interval = Column(Integer, nullable=False, default=0)
    repetition = Column(Integer, nullable=False, default=0)
    due_date = Column(Date, nullable=True, index=True)
    last_seen = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    question = relationship("Question", back_populates="progresses")

    __table_args__ = (
        Index("ix_progress_sid_question", "sid", "question_id", unique=True),
        Index("ix_progress_sid_due", "sid", "due_date"),
    )

    def set_ef(self, value: float) -> None:
        self.ef = float(value)


class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(String(64), nullable=False, index=True)
    mode = Column(String(16), nullable=False)
    params = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_session_sid_started", "sid", "started_at"),
    )


def serialize_choices(choices: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in choices.items() if k in {"A", "B", "C", "D"}}
