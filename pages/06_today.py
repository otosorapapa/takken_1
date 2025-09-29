from __future__ import annotations

import datetime as dt

import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from services.analytics import calc_kpis
from db.session import get_session
from db.models import UserProgress


def get_today_stats(sid: str) -> tuple[int, int]:
    start = dt.datetime.combine(dt.date.today(), dt.time.min)
    end = dt.datetime.combine(dt.date.today(), dt.time.max)
    with get_session() as session:
        answered = (
            session.query(UserProgress)
            .filter(
                UserProgress.sid == sid,
                UserProgress.last_answer.isnot(None),
                UserProgress.last_seen >= start,
                UserProgress.last_seen <= end,
            )
            .count()
        )
        total_time = (
            session.query(UserProgress.answer_time_sec)
            .filter(
                UserProgress.sid == sid,
                UserProgress.answer_time_sec.isnot(None),
                UserProgress.last_seen >= start,
            )
            .all()
        )
    minutes = sum(row[0] for row in total_time) // 60 if total_time else 0
    return answered, minutes


setup_logging()
ensure_session_defaults()
translations = load_translations()
st.session_state["i18n"] = translations

render_header(translations)
render_sidebar(translations)

st.header(translations["app"]["sidebar"]["mode_today"])

state = st.session_state.setdefault(
    "today_state",
    {"goal_questions": 30, "goal_minutes": 30},
)

state["goal_questions"] = st.number_input(
    translations["app"]["today"]["goal_questions"], min_value=5, max_value=200, value=state["goal_questions"], step=5
)
state["goal_minutes"] = st.number_input(
    translations["app"]["today"]["goal_minutes"], min_value=10, max_value=300, value=state["goal_minutes"], step=5
)

answered, minutes = get_today_stats(st.session_state["sid"])
progress_questions = min(1.0, answered / state["goal_questions"]) if state["goal_questions"] else 0
progress_minutes = min(1.0, minutes / state["goal_minutes"]) if state["goal_minutes"] else 0

st.subheader(translations["app"]["today"]["progress"])
st.progress(progress_questions, text=f"問題数: {answered}/{state['goal_questions']}")
st.progress(progress_minutes, text=f"学習時間: {minutes}分/{state['goal_minutes']}分")

kpis = calc_kpis(st.session_state["sid"])
st.write("累計正答率", f"{kpis['accuracy'] * 100:.1f}%")
st.write("直近7日回答数", kpis["week_count"])

st.page_link("pages/01_quick.py", label="クイック演習へ", icon="➡️")
