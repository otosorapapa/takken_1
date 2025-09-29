from __future__ import annotations

import datetime as dt
from typing import Any, Iterable

from sqlalchemy import func

from db.models import Question, UserProgress
from db.session import get_session, init_db
from logic.sm2 import update_sm2
from logic.scheduler import score_priority


def fetch_filtered_questions(filters: dict[str, Any], sid: str, limit: int | None = None) -> list[Question]:
    init_db()
    with get_session() as session:
        query = session.query(Question)
        if "year_range" in filters:
            start_year, end_year = filters["year_range"]
            query = query.filter(Question.year.between(start_year, end_year))
        if "difficulty" in filters:
            difficulty_min, difficulty_max = filters["difficulty"]
            query = query.filter(Question.difficulty.between(difficulty_min, difficulty_max))
        if filters.get("categories"):
            query = query.filter(Question.category.in_(filters["categories"]))
        if filters.get("tags"):
            for tag in filters["tags"]:
                query = query.filter(Question.tags.contains(tag))
        law_filter = filters.get("law_filter", "ignore")
        if law_filter == "include":
            query = query.filter(Question.revised_year.isnot(None))
        elif law_filter == "exclude":
            query = query.filter(Question.revised_year.is_(None))

        ordering = filters.get("ordering", "random")
        if ordering == "random":
            query = query.order_by(func.random())
        elif ordering == "difficulty":
            query = query.order_by(Question.difficulty.desc())
        else:
            query = query.outerjoin(
                UserProgress,
                (UserProgress.question_id == Question.id) & (UserProgress.sid == sid),
            ).order_by(UserProgress.is_correct.asc().nullsfirst(), Question.difficulty.desc())

        if limit:
            query = query.limit(limit)
        return query.all()


def fetch_questions_by_year(year: int) -> list[Question]:
    init_db()
    with get_session() as session:
        return (
            session.query(Question)
            .filter(Question.year == year)
            .order_by(Question.question_no.asc())
            .all()
        )


def fetch_questions_by_categories(categories: Iterable[str], limit: int) -> list[Question]:
    init_db()
    with get_session() as session:
        query = (
            session.query(Question)
            .filter(Question.category.in_(list(categories)))
            .order_by(func.random())
            .limit(limit)
        )
        return query.all()


def get_question(question_id: int, sid: str) -> tuple[Question, UserProgress | None]:
    init_db()
    with get_session() as session:
        question = session.get(Question, question_id)
        progress = (
            session.query(UserProgress)
            .filter(UserProgress.sid == sid, UserProgress.question_id == question_id)
            .one_or_none()
        )
    return question, progress


def record_answer(
    sid: str,
    question_id: int,
    answer: str,
    elapsed: int,
    bookmark: bool = False,
    review: bool = False,
) -> bool:
    init_db()
    with get_session() as session:
        question = session.get(Question, question_id)
        progress = (
            session.query(UserProgress)
            .filter(UserProgress.sid == sid, UserProgress.question_id == question_id)
            .one_or_none()
        )
        if not progress:
            progress = UserProgress(sid=sid, question_id=question_id)
            session.add(progress)

        correct = answer == question.correct
        quality = 4 if correct else 2
        new_ef, new_interval, new_repetition, _ = update_sm2(
            progress.ef, progress.interval, progress.repetition, quality
        )
        progress.last_answer = answer
        progress.is_correct = correct
        progress.answer_time_sec = elapsed
        progress.ef = new_ef
        progress.interval = new_interval
        progress.repetition = new_repetition
        progress.due_date = dt.date.today() + dt.timedelta(days=new_interval)
        progress.last_seen = dt.datetime.utcnow()
        progress.is_bookmarked = bookmark
        progress.is_marked_for_review = review
        session.commit()
    return correct


def build_review_queue(sid: str, limit: int, fallback_filters: dict[str, Any] | None = None) -> list[int]:
    init_db()
    today = dt.date.today()
    with get_session() as session:
        due_items = (
            session.query(UserProgress)
            .filter(
                UserProgress.sid == sid,
                UserProgress.due_date.isnot(None),
                UserProgress.due_date <= today,
            )
            .order_by(UserProgress.ef.asc(), UserProgress.due_date.asc())
            .limit(limit)
            .all()
        )
        question_ids = [item.question_id for item in due_items]

        if len(question_ids) >= limit:
            return question_ids

        # Fallback: select additional questions prioritised by weakness
        remaining = limit - len(question_ids)
        progress_rows = (
            session.query(UserProgress, Question)
            .join(Question, Question.id == UserProgress.question_id)
            .filter(UserProgress.sid == sid)
            .all()
        )
        scored = []
        for progress, question in progress_rows:
            correct_rate = 1.0 if progress.is_correct else 0.0 if progress.is_correct is not None else 0.5
            overdue_days = (today - progress.due_date).days if progress.due_date else 0
            priority = score_priority(correct_rate, max(overdue_days, 0), question.difficulty)
            scored.append((priority, progress.question_id))
        scored.sort(reverse=True)
        for _, qid in scored:
            if qid not in question_ids:
                question_ids.append(qid)
            if len(question_ids) >= limit:
                break

    if len(question_ids) < limit and fallback_filters is not None:
        extra = fetch_filtered_questions(fallback_filters, sid, limit - len(question_ids))
        for question in extra:
            if question.id not in question_ids:
                question_ids.append(question.id)
            if len(question_ids) >= limit:
                break

    return question_ids
