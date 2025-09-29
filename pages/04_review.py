from __future__ import annotations

import time

import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from components.question_card import render_question_card
from services.study import build_review_queue, get_question, record_answer


def ensure_review_state(question_ids: list[int]) -> None:
    state = st.session_state.setdefault(
        "review_state",
        {
            "question_ids": question_ids,
            "current_index": 0,
            "answers": {},
            "results": {},
            "start_time": time.time(),
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
            }
        )


def get_question_dict(question_id: int) -> dict:
    question, progress = get_question(question_id, st.session_state["sid"])
    card_key = f"review_{question_id}"
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


setup_logging()
ensure_session_defaults()
translations = load_translations()
st.session_state["i18n"] = translations

render_header(translations)
filters = render_sidebar(translations)

st.header(translations["app"]["sidebar"]["mode_review"])

if st.button("復習キューを更新", key="review_refresh"):
    queue = build_review_queue(st.session_state["sid"], filters.get("num_questions", 10), filters)
    ensure_review_state(queue)

state = st.session_state.get("review_state")
if not state or not state.get("question_ids"):
    queue = build_review_queue(st.session_state["sid"], filters.get("num_questions", 10), filters)
    ensure_review_state(queue)
    state = st.session_state.get("review_state")

if not state["question_ids"]:
    st.info(translations["app"]["review"]["empty"])
    st.stop()

current_id = state["question_ids"][state["current_index"]]
question_data = get_question_dict(current_id)
result = state["results"].get(current_id)

card = render_question_card(
    question_data,
    translations,
    key_prefix=f"review_{current_id}",
    selected=state["answers"].get(current_id),
    show_feedback=result is not None,
    is_correct=result["correct"] if result else None,
    explanation=question_data.get("explanation"),
    law_references=question_data.get("law_references"),
)

if card["submit_clicked"]:
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
    st.toast("保存しました", icon="✅")

if card["next_clicked"] and state["current_index"] < len(state["question_ids"]) - 1:
    state["current_index"] += 1
    state["start_time"] = time.time()
    st.experimental_rerun()

if card["prev_clicked"] and state["current_index"] > 0:
    state["current_index"] -= 1
    state["start_time"] = time.time()
    st.experimental_rerun()

if len(state["results"]) == len(state["question_ids"]):
    correct_count = sum(1 for r in state["results"].values() if r["correct"])
    total = len(state["question_ids"])
    st.success(f"復習完了: 全{total}問中 {correct_count}問正解")
