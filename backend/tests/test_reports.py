import csv
from io import BytesIO, StringIO

import pytest
from pypdf import PdfReader

from app.routers.reports import _spreadsheet_safe
from app.services.history import save_run


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_formula_leading_text_is_escaped(prefix):
    value = f"{prefix}SUM(1,1)"
    assert _spreadsheet_safe(value) == f"'{value}"


def test_formula_text_after_whitespace_is_escaped():
    assert _spreadsheet_safe("\t=1+1") == "'\t=1+1"


def test_ordinary_text_and_numeric_metrics_are_preserved():
    assert _spreadsheet_safe("Iris dataset") == "Iris dataset"
    assert _spreadsheet_safe(0.92) == 0.92


def test_csv_export_matches_saved_metrics_and_sanitizes_text(
    client, make_user, session_factory
):
    owner = make_user()
    with session_factory() as db:
        run = save_run(
            db,
            owner["user_id"],
            dataset_name="=HYPERLINK(\"https://example.invalid\")",
            target_column="@target",
            feature_columns=["+feature", "height"],
            split_ratio=0.2,
            results=[
                {
                    "algorithm": "-Random Forest",
                    "accuracy": 0.92,
                    "precision": 0.91,
                    "recall": 0.9,
                    "f1_score": 0.905,
                    "roc_auc": 0.95,
                }
            ],
        )
        run_id = run.run_id

    response = client.get(f"/reports/{run_id}/csv", headers=owner["headers"])

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"].endswith(
        f'evaluation-{run_id}.csv"'
    )
    rows = list(csv.reader(StringIO(response.text)))
    assert rows[0][-5:] == ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    assert rows[1][1].startswith("'=HYPERLINK")
    assert rows[1][3] == "'@target"
    assert rows[1][4] == "'+feature | height"
    assert rows[1][6] == "'-Random Forest"
    assert rows[1][-5:] == ["0.92", "0.91", "0.9", "0.905", "0.95"]


def test_pdf_export_contains_run_dataset_configuration_and_metrics(
    client, make_user, make_run
):
    owner = make_user()
    run_id = make_run(owner["user_id"], dataset="Iris sample.csv")

    response = client.get(f"/reports/{run_id}/pdf", headers=owner["headers"])

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].endswith(
        f'evaluation-{run_id}.pdf"'
    )
    assert response.content.startswith(b"%PDF-")
    text = "\n".join(
        page.extract_text() or "" for page in PdfReader(BytesIO(response.content)).pages
    )
    assert "Iris sample.csv" in text
    assert "species" in text
    assert "random_forest" in text
    assert "92.00%" in text


@pytest.mark.parametrize("format_name", ["csv", "pdf"])
def test_report_returns_404_for_unknown_run(client, format_name):
    response = client.get(f"/reports/missing-run/{format_name}")

    assert response.status_code == 404


def test_report_does_not_disclose_another_users_run(client, make_user, make_run):
    owner = make_user("report_owner")
    other = make_user("report_reader")
    run_id = make_run(owner["user_id"])

    response = client.get(f"/reports/{run_id}/csv", headers=other["headers"])

    assert response.status_code == 404


def test_incomplete_run_cannot_be_exported(client, session_factory, make_user):
    owner = make_user()
    with session_factory() as db:
        run = save_run(
            db,
            owner["user_id"],
            dataset_name="pending.csv",
            target_column="target",
            feature_columns=["feature"],
            split_ratio=0.2,
            results=[],
            status="running",
        )
        run_id = run.run_id

    response = client.get(f"/reports/{run_id}/csv", headers=owner["headers"])

    assert response.status_code == 409
