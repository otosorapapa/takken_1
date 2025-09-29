from __future__ import annotations

import datetime as dt
import logging
import logging.handlers
from typing import Any

import pandas as pd
from sqlalchemy import case, func

from db.models import Question, UserProgress
from db.session import get_session, init_db

logger = logging.getLogger(__name__)
if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers):
    handler = logging.handlers.RotatingFileHandler(
        "logs/app.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _answered_filter(query, sid: str):
    return query.filter(UserProgress.sid == sid, UserProgress.last_answer.isnot(None))


def calc_kpis(sid: str) -> dict[str, Any]:
    init_db()
    now = dt.datetime.utcnow()
    week_ago = now - dt.timedelta(days=7)
    month_ago = now - dt.timedelta(days=30)

    with get_session() as session:
        base = session.query(UserProgress).filter(UserProgress.sid == sid)

        total_answered = base.filter(UserProgress.last_answer.isnot(None)).count()
        week_count = (
            base.filter(UserProgress.last_answer.isnot(None), UserProgress.last_seen >= week_ago)
            .count()
        )
        month_count = (
            base.filter(UserProgress.last_answer.isnot(None), UserProgress.last_seen >= month_ago)
            .count()
        )
        accuracy = (
            session.query(
                func.coalesce(
                    func.avg(case((UserProgress.is_correct.is_(True), 1), else_=0)),
                    0,
                )
            )
            .filter(UserProgress.sid == sid, UserProgress.last_answer.isnot(None))
            .scalar()
        )
        avg_time = (
            session.query(func.coalesce(func.avg(UserProgress.answer_time_sec), 0))
            .filter(UserProgress.sid == sid, UserProgress.answer_time_sec.isnot(None))
            .scalar()
        )

        category_stats = (
            session.query(
                Question.category,
                func.coalesce(
                    func.avg(case((UserProgress.is_correct.is_(True), 1), else_=0)),
                    0,
                ).label("accuracy"),
            )
            .join(Question, Question.id == UserProgress.question_id)
            .filter(UserProgress.sid == sid, UserProgress.last_answer.isnot(None))
            .group_by(Question.category)
            .order_by("accuracy")
            .all()
        )

    weakness = [row[0] for row in category_stats[:3]]

    return {
        "total_answered": int(total_answered),
        "week_count": int(week_count),
        "month_count": int(month_count),
        "accuracy": float(accuracy) if accuracy is not None else 0.0,
        "avg_time": float(avg_time) if avg_time is not None else 0.0,
        "weakness_top3": weakness,
    }


def calc_heatmap_data(sid: str) -> pd.DataFrame:
    init_db()
    with get_session() as session:
        rows = (
            session.query(
                Question.year,
                Question.category,
                func.coalesce(
                    func.avg(case((UserProgress.is_correct.is_(True), 1), else_=0)),
                    0,
                ).label("accuracy"),
                func.count(UserProgress.id).label("answered"),
            )
            .join(Question, Question.id == UserProgress.question_id)
            .filter(UserProgress.sid == sid, UserProgress.last_answer.isnot(None))
            .group_by(Question.year, Question.category)
            .all()
        )

    if not rows:
        return pd.DataFrame(columns=["year", "category", "accuracy", "answered"])

    data = [
        {
            "year": row.year,
            "category": row.category,
            "accuracy": float(row.accuracy),
            "answered": int(row.answered),
        }
        for row in rows
    ]
    return pd.DataFrame(data)
