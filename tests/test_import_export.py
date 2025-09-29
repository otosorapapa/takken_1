import csv
import tempfile

from services.export_csv import export_questions_to_csv
from services.import_csv import import_questions_from_csv, validate_row
from db.session import get_session
from db.models import Question


def test_validate_row_success(sample_question_data):
    row = {
        "year": sample_question_data["year"],
        "question_no": sample_question_data["question_no"],
        "category": sample_question_data["category"],
        "difficulty": sample_question_data["difficulty"],
        "question_text": sample_question_data["question_text"],
        "choiceA": "A",
        "choiceB": "B",
        "choiceC": "C",
        "choiceD": "D",
        "correct": "A",
        "explanation": "",
        "law_references": "",
        "revised_year": "",
        "tags": "タグ",
    }
    is_valid, errors = validate_row(row)
    assert is_valid
    assert errors == []


def test_import_and_export(sample_question_data):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=[
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
        ])
        writer.writeheader()
        writer.writerow({
            "year": 2024,
            "question_no": 1,
            "category": "宅建業法",
            "difficulty": 3,
            "question_text": "CSV問題",
            "choiceA": "A",
            "choiceB": "B",
            "choiceC": "C",
            "choiceD": "D",
            "correct": "A",
            "explanation": "",
            "law_references": "",
            "revised_year": "",
            "tags": "タグ",
        })
        csv_path = tmp.name

    inserted, skipped, errors = import_questions_from_csv(csv_path)
    assert inserted == 1
    assert skipped == 0
    assert errors == []

    with get_session() as session:
        count = session.query(Question).count()
    assert count == 1

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_export:
        count_exported = export_questions_to_csv(tmp_export.name)
        tmp_export.seek(0)
        data = tmp_export.read()
    assert count_exported == 1
    assert b"CSV問題" in data
