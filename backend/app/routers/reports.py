"""Download evaluation results as CSV or PDF reports."""

import csv
import re
from io import BytesIO, StringIO
from typing import Any
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_optional_user
from ..models import EvaluationRun, User
from ..services import history as svc


router = APIRouter(prefix="/reports", tags=["reports"])
METRIC_COLUMNS = (
    ("accuracy", "Accuracy"),
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("f1_score", "F1 score"),
    ("roc_auc", "ROC-AUC"),
)


def _report_run(run_id: str, user: User | None, db: Session) -> EvaluationRun:
    run = svc.get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    # Guest runs can be exported without an account. Keep authenticated users'
    # results private and avoid revealing whether another user's run exists.
    if run.user_id is not None and (user is None or run.user_id != user.user_id):
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    if run.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Reports are available after the evaluation is completed",
        )
    return run


def _spreadsheet_safe(value: Any) -> Any:
    """Neutralize formula-like text while leaving numeric metrics numeric."""
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value

    text = str(value)
    if re.match(r"^[\s\x00-\x1f]*[=+\-@]", text):
        return "'" + text
    return text


def _timestamp(run: EvaluationRun) -> str:
    value = run.timestamp.isoformat()
    return value + "Z" if run.timestamp.tzinfo is None else value


def _metric_text(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.2f}%"


def _csv_content(run: EvaluationRun) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(
        [
            "run_id",
            "dataset_name",
            "timestamp",
            "target_column",
            "feature_columns",
            "split_ratio",
            "algorithm",
            *(column for column, _ in METRIC_COLUMNS),
        ]
    )

    features = " | ".join(str(feature) for feature in run.feature_columns)
    for result in run.results:
        writer.writerow(
            [
                _spreadsheet_safe(run.run_id),
                _spreadsheet_safe(run.dataset_name),
                _spreadsheet_safe(_timestamp(run)),
                _spreadsheet_safe(run.target_column),
                _spreadsheet_safe(features),
                run.split_ratio,
                _spreadsheet_safe(result.algorithm_name),
                *(getattr(result, column) for column, _ in METRIC_COLUMNS),
            ]
        )
    return output.getvalue()


def _pdf_content(run: EvaluationRun) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        pageCompression=0,
        title=f"Evaluation report {run.run_id}",
    )

    safe = lambda value: escape(str(value))
    feature_text = ", ".join(str(feature) for feature in run.feature_columns)
    story = [
        Paragraph("Model evaluation report", styles["Title"]),
        Spacer(1, 5 * mm),
        Paragraph(f"<b>Dataset:</b> {safe(run.dataset_name)}", styles["BodyText"]),
        Paragraph(f"<b>Run ID:</b> {safe(run.run_id)}", styles["BodyText"]),
        Paragraph(f"<b>Completed:</b> {safe(_timestamp(run))}", styles["BodyText"]),
        Paragraph(f"<b>Target column:</b> {safe(run.target_column)}", styles["BodyText"]),
        Paragraph(f"<b>Features:</b> {safe(feature_text or 'None')}", styles["BodyText"]),
        Paragraph(
            f"<b>Test split:</b> {run.split_ratio * 100:.1f}%",
            styles["BodyText"],
        ),
        Spacer(1, 6 * mm),
    ]

    table_data = [["Algorithm", *(label for _, label in METRIC_COLUMNS)]]
    for result in run.results:
        table_data.append(
            [
                Paragraph(safe(result.algorithm_name), styles["BodyText"]),
                *(_metric_text(getattr(result, column)) for column, _ in METRIC_COLUMNS),
            ]
        )

    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46b8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d6d7e4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6fb")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    best = max(
        run.results,
        key=lambda result: (
            result.f1_score is not None,
            result.f1_score if result.f1_score is not None else -1,
            result.algorithm_name.casefold(),
        ),
        default=None,
    )
    if best is None or best.f1_score is None:
        summary = f"Evaluation completed for {len(run.results)} algorithm(s). F1 score was unavailable for comparison."
    else:
        summary = (
            f"Evaluation completed for {len(run.results)} algorithm(s). "
            f"{best.algorithm_name} achieved the highest F1 score at "
            f"{_metric_text(best.f1_score)}."
        )
    story.append(Paragraph(f"<b>Summary:</b> {safe(summary)}", styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()


def _filename(run_id: str, extension: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", run_id)
    return f"evaluation-{safe_id}.{extension}"


@router.get("/{run_id}/csv")
def export_csv(
    run_id: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    run = _report_run(run_id, user, db)
    return Response(
        content=_csv_content(run),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{_filename(run.run_id, "csv")}"'
        },
    )


@router.get("/{run_id}/pdf")
def export_pdf(
    run_id: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    run = _report_run(run_id, user, db)
    return Response(
        content=_pdf_content(run),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{_filename(run.run_id, "pdf")}"'
        },
    )
