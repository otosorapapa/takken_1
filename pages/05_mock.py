from __future__ import annotations

import pandas as pd
import time

import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from components.question_card import render_question_card
from components.timer import render_countdown, reset_countdown
from logic.sampling import sample_mock
from services.study import get_question, record_answer
from db.session import get_session
from db.models import Question

MOCK_DURATION = 120 * 60


def load_questions_df() -> pd.DataFrame:
    with get_session() as session:
        questions = session.query(Question).all()
    rows = [
        {
            "id": q.id,
            "year": q.year,
            "category": q.category,
            "difficulty": q.difficulty,
        }
        for q in questions
    ]
    return pd.DataFrame(rows)


def ensure_mock_state(question_ids: list[int]) -> None:
    state = st.session_state.setdefault(
        "mock_state",
        {
            "question_ids": question_ids,
            "current_index": 0,
            "answers": {},
            "results": {},
            "start_time": time.time(),
            "completed": False,
        },
    )
    if state["question_ids"] != question_ids:
        state.update(
            {
                "question_ids": question_ids,
                "current_index": 0,
                "answers": {},
                "results": {},
                "start_time": time.time(),
                "completed": False,
            }
        )


def get_question_dict(question_id: int) -> dict:
    question, progress = get_question(question_id, st.session_state["sid"])
    card_key = f"mock_{question_id}"
    st.session_state.setdefault(f"{card_key}_bookmark", progress.is_bookmarked if progress else False)
    st.session_state.setdefault(f"{card_key}_review", progress.is_marked_for_review if progress else False)
    return {
        "id": question.id,
        "year": question.year,
        "question_no": question.question_no,
        "category": question.category,
        "difficulty": question.difficulty,
        "question_text": question.question_text,
        "choices": question.choices,
        "correct": question.correct,
        "explanation": question.explanation,
        "law_references": question.law_references,
    }


def finish_mock(state: dict) -> None:
    state["completed"] = True
    reset_countdown("mock_exam")


setup_logging()
ensure_session_defaults()
translations = load_translations()
st.session_state["i18n"] = translations

render_header(translations)
render_sidebar(translations)

st.header(translations["app"]["mock"]["title"])

if st.button(translations["app"]["mock"]["start"], key="mock_start") or "mock_state" in st.session_state:
    df = load_questions_df()
    if df.empty:
        st.warning("問題データが不足しています")
        st.stop()

    if "mock_state" not in st.session_state:
        question_ids = sample_mock(df)
        ensure_mock_state(question_ids)
        st.session_state["mock_state"]["start_time"] = time.time()
    state = st.session_state["mock_state"]

    remaining = render_countdown("mock_exam", MOCK_DURATION, translations["app"]["mock"]["remaining"])
    if remaining == 0 and not state["completed"]:
        finish_mock(state)
        st.warning("時間切れです。自動で採点します。")

    if state["completed"]:
        pass
    else:
        current_id = state["question_ids"][state["current_index"]]
        question_data = get_question_dict(current_id)
        result = state["results"].get(current_id)
        card = render_question_card(
            question_data,
            translations,
            key_prefix=f"mock_{current_id}",
            selected=state["answers"].get(current_id),
            show_feedback=result is not None,
            is_correct=result["correct"] if result else None,
            explanation=None,
            law_references=None,
            disabled=state["completed"],
        )

        if card["submit_clicked"] and not state["completed"]:
            elapsed = int(time.time() - state["start_time"])
            correct = record_answer(
                st.session_state["sid"],
                current_id,
                card["choice"],
                elapsed,
                bookmark=card["bookmark"],
                review=card["mark_review"],
            )
            state["answers"][current_id] = card["choice"]
            state["results"][current_id] = {"correct": correct, "elapsed": elapsed}
            st.toast("回答を保存しました", icon="✅")

        if card["next_clicked"] and state["current_index"] < len(state["question_ids"]) - 1:
            state["current_index"] += 1
            st.experimental_rerun()

        if card["prev_clicked"] and state["current_index"] > 0:
            state["current_index"] -= 1
            st.experimental_rerun()

        if len(state["results"]) == len(state["question_ids"]):
            finish_mock(state)
            st.success("全問回答しました。採点します。")

    if state["completed"]:
        correct_count = sum(1 for r in state["results"].values() if r["correct"])
        total = len(state["question_ids"])
        score = correct_count
        st.subheader("結果")
        st.metric("得点", f"{score} / {total}")
        accuracy = (score / total) * 100 if total else 0
        st.metric("正答率", f"{accuracy:.1f}%")
        incorrect = [qid for qid, res in state["results"].items() if not res["correct"]]
        if incorrect:
            st.write("誤答ノート")
            for qid in incorrect:
                q = get_question_dict(qid)
                st.markdown(f"- {q['year']}年 第{q['question_no']}問 {q['category']}")
        if st.button("模試をリセット", key="mock_reset"):
            st.session_state.pop("mock_state")
            reset_countdown("mock_exam")
            st.experimental_rerun()
else:
    st.info("模試を開始するにはボタンを押してください。")
