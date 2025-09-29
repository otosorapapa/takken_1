from __future__ import annotations

import time
from typing import Any

import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from components.question_card import render_question_card
from services.study import fetch_filtered_questions, get_question, record_answer


def ensure_quick_state(question_ids: list[int]) -> None:
    state = st.session_state.setdefault(
        "quick_state",
        {
            "question_ids": [],
            "current_index": 0,
            "answers": {},
            "results": {},
            "start_time": time.time(),
        },
    )
    if question_ids and state["question_ids"] != question_ids:
        state.update(
            {
                "question_ids": question_ids,
                "current_index": 0,
                "answers": {},
                "results": {},
                "start_time": time.time(),
            }
        )


def get_question_dict(question_id: int) -> dict[str, Any]:
    question, progress = get_question(question_id, st.session_state["sid"])
    card_key = f"quick_{question_id}"
    if progress:
        st.session_state.setdefault(f"{card_key}_bookmark", progress.is_bookmarked)
        st.session_state.setdefault(f"{card_key}_review", progress.is_marked_for_review)
    else:
        st.session_state.setdefault(f"{card_key}_bookmark", False)
        st.session_state.setdefault(f"{card_key}_review", False)

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

st.header(translations["app"]["sidebar"]["mode_quick"])

if st.button("問題セットを更新", key="quick_refresh"):
    questions = fetch_filtered_questions(filters, st.session_state["sid"], filters.get("num_questions", 10))
    ensure_quick_state([q.id for q in questions])

state = st.session_state.get("quick_state")
if not state or not state.get("question_ids"):
    questions = fetch_filtered_questions(filters, st.session_state["sid"], filters.get("num_questions", 10))
    ensure_quick_state([q.id for q in questions])
    state = st.session_state.get("quick_state")

if not state["question_ids"]:
    st.info("条件に合致する問題がありません")
    st.stop()

current_id = state["question_ids"][state["current_index"]]
question_data = get_question_dict(current_id)
card_key = f"quick_{current_id}"
selected = state["answers"].get(current_id)
result = state["results"].get(current_id)

card_result = render_question_card(
    question_data,
    translations,
    key_prefix=card_key,
    selected=selected,
    show_feedback=result is not None,
    is_correct=result["correct"] if result else None,
    explanation=question_data.get("explanation"),
    law_references=question_data.get("law_references"),
)

if card_result["submit_clicked"]:
    elapsed = int(time.time() - state["start_time"])
    correct = record_answer(
        st.session_state["sid"],
        current_id,
        card_result["choice"],
        elapsed,
        bookmark=card_result["bookmark"],
        review=card_result["mark_review"],
    )
    state["answers"][current_id] = card_result["choice"]
    state["results"][current_id] = {"correct": correct, "elapsed": elapsed}
    st.toast("保存しました", icon="✅")

if card_result["next_clicked"] and state["current_index"] < len(state["question_ids"]) - 1:
    state["current_index"] += 1
    state["start_time"] = time.time()
    st.experimental_rerun()

if card_result["prev_clicked"] and state["current_index"] > 0:
    state["current_index"] -= 1
    state["start_time"] = time.time()
    st.experimental_rerun()

if len(state["results"]) == len(state["question_ids"]):
    correct_count = sum(1 for data in state["results"].values() if data["correct"])
    total = len(state["question_ids"])
    accuracy = (correct_count / total) * 100 if total else 0
    st.success(f"全{total}問中 {correct_count}問正解 (正答率 {accuracy:.1f}%)")
    st.write("誤答ノート")
    for qid, data in state["results"].items():
        if not data["correct"]:
            q = get_question_dict(qid)
            st.markdown(f"- {q['year']}年 第{q['question_no']}問 {q['category']}")

    if st.button("結果をリセット", key="quick_reset"):
        ensure_quick_state(state["question_ids"])
        st.experimental_rerun()
