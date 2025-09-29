from __future__ import annotations

from typing import Any

import streamlit as st


def render_question_card(
    question: dict[str, Any],
    i18n: dict[str, Any],
    *,
    key_prefix: str = "question",
    selected: str | None = None,
    show_feedback: bool = False,
    is_correct: bool | None = None,
    explanation: str | None = None,
    law_references: str | None = None,
    timer_text: str | None = None,
    disabled: bool = False,
) -> dict[str, Any]:
    card_i18n = i18n["app"]["question_card"]

    st.markdown(
        f"""
        <div class="question-meta">
            <span class="badge">{card_i18n['year']}: {question.get('year')}</span>
            <span class="badge">{card_i18n['category']}: {question.get('category')}</span>
            <span class="badge">{card_i18n['difficulty']}: {question.get('difficulty')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"## {question.get('question_no')}. {question.get('question_text')}")

    if timer_text:
        st.caption(f"⏱️ {card_i18n['time_elapsed']}: {timer_text}")

    options = ["A", "B", "C", "D"]
    radio_key = f"{key_prefix}_choice"
    current_index = options.index(selected) if selected in options else None

    choice = st.radio(
        "",
        options,
        index=current_index,
        format_func=lambda x: f"{x}. {question['choices'][x]}",
        key=radio_key,
        disabled=disabled,
        horizontal=False,
        label_visibility="collapsed",
    )

    col_action = st.columns(3)
    with col_action[0]:
        bookmark = st.checkbox(card_i18n["bookmark"], key=f"{key_prefix}_bookmark")
    with col_action[1]:
        mark_review = st.checkbox(card_i18n["mark_for_review"], key=f"{key_prefix}_review")
    with col_action[2]:
        save_clicked = st.button(card_i18n["save"], key=f"{key_prefix}_save")

    submit_col, next_col, prev_col = st.columns([2, 1, 1])
    with submit_col:
        submit_clicked = st.button(card_i18n["submit"], key=f"{key_prefix}_submit", use_container_width=True)
    with next_col:
        next_clicked = st.button(card_i18n["next"], key=f"{key_prefix}_next")
    with prev_col:
        prev_clicked = st.button(card_i18n["prev"], key=f"{key_prefix}_prev")

    if show_feedback and is_correct is not None:
        if is_correct:
            st.success(card_i18n["result_correct"])
        else:
            st.error(card_i18n["result_incorrect"])
        st.info(f"{card_i18n['correct_answer']}: {question.get('correct')}")
        if explanation:
            st.markdown(f"**{card_i18n['explanation']}**\n\n{explanation}")
        if law_references:
            st.caption(f"{card_i18n['law_reference']}: {law_references}")

    return {
        "choice": choice,
        "bookmark": bookmark,
        "mark_review": mark_review,
        "submit_clicked": submit_clicked,
        "next_clicked": next_clicked,
        "prev_clicked": prev_clicked,
        "save_clicked": save_clicked,
    }
