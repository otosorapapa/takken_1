from __future__ import annotations

import json
import logging
import logging.handlers
import uuid
from pathlib import Path

import streamlit as st
from sqlalchemy import func

from components.theme import THEMES, apply_theme
from db.models import Question
from db.session import get_session, init_db
from services.analytics import calc_kpis

st.set_page_config(page_title="宅建10年ドリル", layout="wide")


def setup_logging() -> None:
    logger = logging.getLogger()
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers):
        handler = logging.handlers.RotatingFileHandler(
            "logs/app.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@st.cache_data(ttl=600)
def load_translations(lang: str = "ja") -> dict:
    path = Path("i18n") / f"{lang}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=600)
def get_year_bounds() -> tuple[int, int]:
    init_db()
    with get_session() as session:
        result = session.query(func.min(Question.year), func.max(Question.year)).one()
    min_year = result[0] or 2015
    max_year = result[1] or 2024
    return int(min_year), int(max_year)


@st.cache_data(ttl=600)
def get_categories() -> list[str]:
    init_db()
    with get_session() as session:
        rows = session.query(Question.category).distinct().order_by(Question.category).all()
    return [row[0] for row in rows] or ["権利関係", "宅建業法", "法令上の制限", "税・その他"]


def ensure_session_defaults() -> None:
    if "sid" not in st.session_state:
        st.session_state["sid"] = str(uuid.uuid4())
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"
    if "filters" not in st.session_state:
        min_year, max_year = get_year_bounds()
        st.session_state["filters"] = {
            "num_questions": 10,
            "difficulty": (1, 5),
            "year_range": (min_year, max_year),
            "categories": [],
            "ordering": "random",
            "law_filter": "ignore",
            "tags": [],
        }


def render_sidebar(translations: dict) -> dict:
    sidebar = translations["app"]["sidebar"]
    filters = st.session_state["filters"]

    st.sidebar.title(translations["app"]["title"])
    st.sidebar.caption(translations["app"]["description"])

    st.sidebar.subheader("ナビゲーション")
    st.sidebar.page_link("app.py", label="ホーム")
    st.sidebar.page_link("pages/01_quick.py", label=sidebar["mode_quick"])
    st.sidebar.page_link("pages/02_year.py", label=sidebar["mode_year"])
    st.sidebar.page_link("pages/03_category.py", label=sidebar["mode_category"])
    st.sidebar.page_link("pages/04_review.py", label=sidebar["mode_review"])
    st.sidebar.page_link("pages/05_mock.py", label=sidebar["mode_mock"])
    st.sidebar.page_link("pages/06_today.py", label=sidebar["mode_today"])
    st.sidebar.page_link("pages/07_dashboard.py", label=sidebar["mode_dashboard"])
    st.sidebar.page_link("pages/99_admin.py", label=sidebar["mode_admin"])

    st.sidebar.divider()
    st.sidebar.subheader("フィルタ")

    filters["num_questions"] = st.sidebar.selectbox(
        sidebar["num_questions"], [5, 10, 20, 50, 100], index=[5, 10, 20, 50, 100].index(filters["num_questions"])
    )
    filters["difficulty"] = st.sidebar.slider(
        sidebar["difficulty"], 1, 5, filters["difficulty"], step=1
    )
    year_min, year_max = get_year_bounds()
    filters["year_range"] = st.sidebar.slider(
        sidebar["year_range"], year_min, year_max, filters["year_range"], step=1
    )
    categories = get_categories()
    filters["categories"] = st.sidebar.multiselect(
        sidebar["category"], categories, default=filters["categories"]
    )
    filters["ordering"] = st.sidebar.selectbox(
        sidebar["ordering"],
        ["random", "difficulty", "weakness"],
        format_func=lambda x: sidebar[f"ordering_{x}"] if f"ordering_{x}" in sidebar else x,
        index=["random", "difficulty", "weakness"].index(filters["ordering"]),
    )
    filters["law_filter"] = st.sidebar.selectbox(
        sidebar["law_filter"],
        ["include", "exclude", "ignore"],
        format_func=lambda x: sidebar[f"law_filter_{x}"],
        index=["include", "exclude", "ignore"].index(filters["law_filter"]),
    )
    tag_input = st.sidebar.text_input(sidebar["tag_filter"], value=",".join(filters["tags"]))
    filters["tags"] = [tag.strip() for tag in tag_input.split(",") if tag.strip()]

    if st.sidebar.button(sidebar["reset"]):
        min_year, max_year = get_year_bounds()
        filters.update(
            {
                "num_questions": 10,
                "difficulty": (1, 5),
                "year_range": (min_year, max_year),
                "categories": [],
                "ordering": "random",
                "law_filter": "ignore",
                "tags": [],
            }
        )
        st.experimental_rerun()

    st.session_state["filters"] = filters
    return filters


def render_header(translations: dict) -> None:
    header = translations["app"]["header"]
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(translations["app"]["title"])
    with col2:
        theme_key = st.selectbox(
            "テーマ",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["theme"]),
            format_func=lambda x: header[f"theme_{x}"] if f"theme_{x}" in header else x,
        )
        st.session_state["theme"] = theme_key
    with col3:
        kpis = calc_kpis(st.session_state["sid"])
        st.metric(header["summary_answered"], kpis["week_count"])
        accuracy_pct = f"{kpis['accuracy'] * 100:.0f}%" if kpis["accuracy"] else "0%"
        st.metric(header["summary_accuracy"], accuracy_pct)

    apply_theme(st.session_state["theme"])


def render_shortcuts(translations: dict) -> None:
    shortcuts = translations["app"]["shortcuts"]
    st.subheader(shortcuts["title"])
    cols = st.columns(3)
    items = [
        shortcuts["answer"],
        shortcuts["submit"],
        shortcuts["next"],
        shortcuts["bookmark"],
        shortcuts["retry"],
        shortcuts["save"],
    ]
    for idx, text in enumerate(items):
        with cols[idx % 3]:
            st.write(f"- {text}")


def main() -> None:
    setup_logging()
    init_db()
    ensure_session_defaults()
    translations = load_translations()
    st.session_state["i18n"] = translations

    render_header(translations)
    filters = render_sidebar(translations)

    st.success("フィルタが適用されました")
    st.write("現在の条件:")
    st.json(filters)

    st.markdown("### アプリ概要")
    st.write(translations["app"]["description"])

    render_shortcuts(translations)


if __name__ == "__main__":
    main()
