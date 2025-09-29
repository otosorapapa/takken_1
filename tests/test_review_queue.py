import datetime as dt

from services.study import build_review_queue
from db.models import Question, UserProgress
from db.session import get_session


def test_build_review_queue(sample_question_data, sid):
    with get_session() as session:
        question = Question(**sample_question_data)
        session.add(question)
        session.flush()
        progress = UserProgress(
            sid=sid,
            question_id=question.id,
            last_answer="B",
            is_correct=False,
            answer_time_sec=20,
            ef=1.5,
            interval=1,
            repetition=1,
            due_date=dt.date.today() - dt.timedelta(days=1),
            last_seen=dt.datetime.utcnow() - dt.timedelta(days=2),
        )
        session.add(progress)

    queue = build_review_queue(sid, limit=5)
    assert question.id in queue
