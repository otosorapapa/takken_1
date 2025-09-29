from __future__ import annotations

import json
import tempfile
from typing import Any

import pandas as pd
import streamlit as st

from app import ensure_session_defaults, load_translations, render_header, render_sidebar, setup_logging
from services.export_csv import export_questions_to_csv
from services.import_csv import import_questions_from_csv
from db.session import get_session
from db.models import Question, UserProgress

COLUMNS = [
    "year",
    "question_no",
    "category",
    "difficulty",
    "question_text",
    "choiceA",
    "choiceB",
    "choiceC",
    "choiceD",
    "correct",
    "explanation",
    "law_references",
    "revised_year",
    "tags",
]


def load_json_to_csv(data: list[dict[str, Any]]) -> str:
    rows = []
    for item in data:
        row = {
            "year": item["year"],
            "question_no": item["question_no"],
            "category": item["category"],
            "difficulty": item["difficulty"],
            "question_text": item["question_text"],
            "choiceA": item["choices"]["A"],
            "choiceB": item["choices"]["B"],
            "choiceC": item["choices"]["C"],
            "choiceD": item["choices"]["D"],
            "correct": item["correct"],
            "explanation": item.get("explanation", ""),
            "law_references": item.get("law_references", ""),
            "revised_year": item.get("revised_year", ""),
            "tags": item.get("tags", ""),
        }
        rows.append(row)
    df = pd.DataFrame(rows, columns=COLUMNS)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)
    return tmp.name


def build_download_button(label: str, filters: dict[str, Any] | None = None, filename: str = "questions.csv") -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        count = export_questions_to_csv(tmp.name, filters)
        tmp.seek(0)
        data = tmp.read()
    st.download_button(label, data=data, file_name=filename, mime="text/csv")
    st.caption(f"件数: {count}")


def get_bookmarked_question_ids() -> list[int]:
    with get_session() as session:
        rows = session.query(UserProgress.question_id).filter(UserProgress.is_bookmarked.is_(True)).all()
    return [row[0] for row in rows]


def get_incorrect_question_ids() -> list[int]:
    with get_session() as session:
        rows = session.query(UserProgress.question_id).filter(UserProgress.is_correct.is_(False)).all()
    return [row[0] for row in rows]


def perform_bulk_update(category: str, difficulty: int) -> int:
    with get_session() as session:
        updated = (
            session.query(Question)
            .filter(Question.category == category)
            .update({Question.difficulty: difficulty}, synchronize_session=False)
        )
    return updated


setup_logging()
ensure_session_defaults()
translations = load_translations()
st.session_state["i18n"] = translations

render_header(translations)
render_sidebar(translations)

st.header(translations["app"]["sidebar"]["mode_admin"])

uploaded = st.file_uploader("CSV / JSON", type=["csv", "json"])
if uploaded is not None:
    if uploaded.type == "text/csv" or uploaded.name.endswith(".csv"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        inserted, skipped, errors = import_questions_from_csv(tmp_path)
        st.success(f"{inserted}件を取り込みました / スキップ {skipped}件")
        if errors:
            st.error("エラーが発生しました")
            st.json(errors)
    else:
        content = json.loads(uploaded.getvalue())
        if isinstance(content, dict):
            content = [content]
        tmp_path = load_json_to_csv(content)
        inserted, skipped, errors = import_questions_from_csv(tmp_path)
        st.success(f"{inserted}件を取り込みました / スキップ {skipped}件")
        if errors:
            st.error("エラーが発生しました")
            st.json(errors)

st.divider()

st.subheader("エクスポート")
build_download_button("全問題をダウンロード")
bookmarked_ids = get_bookmarked_question_ids()
if bookmarked_ids:
    build_download_button("ブックマークのみダウンロード", {"ids": bookmarked_ids}, filename="bookmarks.csv")
incorrect_ids = get_incorrect_question_ids()
if incorrect_ids:
    build_download_button("誤答のみダウンロード", {"ids": incorrect_ids}, filename="incorrect.csv")

st.divider()

st.subheader("一括編集")
category = st.selectbox("分野", ["権利関係", "宅建業法", "法令上の制限", "税・その他"])
new_difficulty = st.slider("難易度再設定", 1, 5, 3)
if st.button("更新を実行"):
    updated = perform_bulk_update(category, new_difficulty)
    st.success(f"{updated}件を更新しました")
