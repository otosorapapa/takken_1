from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from services.analytics import calc_heatmap_data, calc_kpis
from db.session import get_session
from db.models import Question, UserProgress


def load_progress_df(sid: str) -> pd.DataFrame:
    with get_session() as session:
        rows = (
            session.query(UserProgress, Question)
            .join(Question, Question.id == UserProgress.question_id)
            .filter(UserProgress.sid == sid, UserProgress.last_answer.isnot(None))
            .all()
        )
    data = []
    for progress, question in rows:
        data.append(
            {
                "last_seen": progress.last_seen.date(),
                "category": question.category,
                "year": question.year,
                "difficulty": question.difficulty,
                "is_correct": 1 if progress.is_correct else 0,
                "answer_time_sec": progress.answer_time_sec or 0,
            }
        )
    return pd.DataFrame(data)


setup_logging()
ensure_session_defaults()
translations = load_translations()
st.session_state["i18n"] = translations

render_header(translations)
render_sidebar(translations)

st.header(translations["app"]["sidebar"]["mode_dashboard"])

sid = st.session_state["sid"]
progress_df = load_progress_df(sid)
heatmap_df = calc_heatmap_data(sid)
kpis = calc_kpis(sid)

col1, col2, col3, col4 = st.columns(4)
col1.metric(translations["app"]["dashboard"]["kpi_total"], kpis["total_answered"])
col2.metric(translations["app"]["dashboard"]["kpi_week"], kpis["week_count"])
col3.metric(translations["app"]["dashboard"]["kpi_month"], kpis["month_count"])
col4.metric(translations["app"]["dashboard"]["kpi_accuracy"], f"{kpis['accuracy'] * 100:.1f}%")

st.metric(translations["app"]["dashboard"]["kpi_time"], f"{kpis['avg_time']:.1f} 秒")
if kpis["weakness_top3"]:
    st.write(translations["app"]["dashboard"]["kpi_weakness"], ", ".join(kpis["weakness_top3"]))

if not progress_df.empty:
    daily = progress_df.groupby("last_seen").size().reset_index(name="count")
    daily_fig = px.line(daily, x="last_seen", y="count", markers=True)
    st.plotly_chart(daily_fig, use_container_width=True)

    category_accuracy = progress_df.groupby("category")["is_correct"].mean().reset_index()
    category_fig = px.bar(category_accuracy, x="category", y="is_correct", title=translations["app"]["dashboard"]["chart_category_accuracy"])
    st.plotly_chart(category_fig, use_container_width=True)

    year_dist = progress_df.groupby("year").size().reset_index(name="count")
    year_fig = px.bar(year_dist, x="year", y="count", title=translations["app"]["dashboard"]["chart_year_distribution"])
    st.plotly_chart(year_fig, use_container_width=True)

    difficulty_accuracy = progress_df.groupby("difficulty")["is_correct"].mean().reset_index()
    diff_fig = px.bar(
        difficulty_accuracy,
        x="difficulty",
        y="is_correct",
        title=translations["app"]["dashboard"]["chart_difficulty"],
    )
    st.plotly_chart(diff_fig, use_container_width=True)
else:
    st.info("まだ十分な学習データがありません")

if not heatmap_df.empty:
    pivot = heatmap_df.pivot(index="category", columns="year", values="accuracy")
    heatmap_fig = px.imshow(pivot, text_auto=True, aspect="auto", title="分野×年度 正答率")
    st.plotly_chart(heatmap_fig, use_container_width=True)

exam_date = st.date_input("試験日", dt.date.today() + dt.timedelta(days=180))
remaining_days = (exam_date - dt.date.today()).days
suggested = max(0, remaining_days) * 25
st.write(
    translations["app"]["dashboard"]["countdown"],
    f"{max(0, remaining_days)}日",
)
st.write(translations["app"]["dashboard"]["suggested_volume"], f"1日あたり {suggested // max(1, remaining_days or 1)}問 目安")
