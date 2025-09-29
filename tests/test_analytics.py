import datetime as dt

from services.analytics import calc_heatmap_data, calc_kpis
from db.models import Question, UserProgress
from db.session import get_session


def test_calc_kpis_and_heatmap(sample_question_data, sid):
    with get_session() as session:
        question = Question(**sample_question_data)
        session.add(question)
        session.flush()
        progress = UserProgress(
            sid=sid,
            question_id=question.id,
            last_answer="A",
            is_correct=True,
            answer_time_sec=42,
            last_seen=dt.datetime.utcnow(),
            due_date=dt.date.today(),
        )
        session.add(progress)

    kpis = calc_kpis(sid)
    assert kpis["total_answered"] == 1
    assert kpis["accuracy"] == 1

    heatmap = calc_heatmap_data(sid)
    assert not heatmap.empty
    assert heatmap.iloc[0]["accuracy"] == 1
