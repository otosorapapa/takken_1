from __future__ import annotations

import time

import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from components.question_card import render_question_card
from services.study import fetch_questions_by_categories, get_question, record_answer

CATEGORIES = ["権利関係", "宅建業法", "法令上の制限", "税・その他"]


def ensure_category_state(question_ids: list[int]) -> None:
    state = st.session_state.setdefault(
        "category_state",
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
    card_key = f"category_{question_id}"
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
render_sidebar(translations)

st.header(translations["app"]["sidebar"]["mode_category"])

selected_categories = st.multiselect("分野を選択", CATEGORIES, default=CATEGORIES[:2])
count = st.selectbox("出題数", [5, 10, 15, 20], index=1)

if st.button("出題する", key="category_fetch"):
    questions = fetch_questions_by_categories(selected_categories or CATEGORIES, count)
    ensure_category_state([q.id for q in questions])

state = st.session_state.get("category_state")
if not state or not state.get("question_ids"):
    questions = fetch_questions_by_categories(selected_categories or CATEGORIES, count)
    ensure_category_state([q.id for q in questions])
    state = st.session_state.get("category_state")

if not state["question_ids"]:
    st.info("条件に合致する問題がありません")
    st.stop()

current_id = state["question_ids"][state["current_index"]]
question_data = get_question_dict(current_id)
result = state["results"].get(current_id)

card = render_question_card(
    question_data,
    translations,
    key_prefix=f"category_{current_id}",
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
    st.success(f"全{total}問中 {correct_count}問正解")
