from services.study import record_answer
from db.models import Question, UserProgress
from db.session import get_session


def test_record_answer_updates_progress(sample_question_data, sid):
    with get_session() as session:
        q = Question(**sample_question_data)
        session.add(q)
        session.flush()
        question_id = q.id

    correct = record_answer(sid, question_id, "A", 30, bookmark=True, review=True)
    assert correct is True

    with get_session() as session:
        progress = session.query(UserProgress).filter_by(sid=sid, question_id=question_id).one()
    assert progress.is_bookmarked is True
    assert progress.is_marked_for_review is True
