
"""History service (MLE-F-025/026/027). Pure functions: no HTTP concerns here."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import AlgorithmResult, EvaluationRun


def new_run_id() -> str:
    return "run_" + uuid.uuid4().hex[:12]


def save_run(
    db: Session,
    user_id: Optional[int],
    *,
    dataset_name: str,
    target_column: str,
    feature_columns: list,
    split_ratio: float,
    results: list[dict],
    status: str = "completed",
    timestamp: Optional[datetime] = None,
) -> EvaluationRun:
    """Persist a finished evaluation (MLE-F-025).

    Call this from the POST /evaluations endpoint right after metrics are computed:
        save_run(db, user.user_id if user else None, ...)
    user_id=None stores a guest-scoped run: it can be fetched by the guest flow but
    never appears in anyone's history.
    """
    run = EvaluationRun(
        run_id=new_run_id(),
        user_id=user_id,
        dataset_name=dataset_name,
        target_column=target_column,
        feature_columns=list(feature_columns),
        split_ratio=split_ratio,
        status=status,
    )

    if timestamp is not None:
        run.timestamp = timestamp

    for r in results:
        run.results.append(
            AlgorithmResult(
                algorithm_name=r["algorithm"],
                accuracy=r.get("accuracy"),
                precision=r.get("precision"),
                recall=r.get("recall"),
                f1_score=r.get("f1_score"),
                roc_auc=r.get("roc_auc"),
                confusion_matrix=r.get("confusion_matrix"),
                serialized_metrics=r.get("serialized_metrics"),
            )
        )

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_runs(db: Session, user_id: int, limit: int = 50, offset: int = 0):
    """Only the caller's runs, newest first (MLE-F-026)."""
    where = EvaluationRun.user_id == user_id

    total = db.scalar(
        select(func.count()).select_from(EvaluationRun).where(where)
    ) or 0

    rows = db.scalars(
        select(EvaluationRun)
        .where(where)
        .order_by(
            EvaluationRun.timestamp.desc(),
            EvaluationRun.run_id.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()

    return rows, total


def get_run(db: Session, run_id: str) -> Optional[EvaluationRun]:
    return db.get(EvaluationRun, run_id)


def delete_run(db: Session, run: EvaluationRun) -> None:
    """Deletes the run and its AlgorithmResult rows (cascade) (MLE-F-027)."""
    db.delete(run)
    db.commit()


def _metrics(r: AlgorithmResult) -> dict:
    return {
        "algorithm": r.algorithm_name,
        "accuracy": r.accuracy,
        "precision": r.precision,
        "recall": r.recall,
        "f1_score": r.f1_score,
        "roc_auc": r.roc_auc,
    }


def _iso(ts: datetime) -> str:
    return ts.isoformat() + "Z"  # stored as naive UTC


def run_summary(run: EvaluationRun) -> dict:
    return {
        "run_id": run.run_id,
        "dataset_name": run.dataset_name,
        "timestamp": _iso(run.timestamp),
        "status": run.status,
        "algorithms": [r.algorithm_name for r in run.results],
        "metrics": [_metrics(r) for r in run.results],
    }


def run_detail(run: EvaluationRun) -> dict:
    detail = run_summary(run)
    detail.update(
        {
            "target_column": run.target_column,
            "feature_columns": run.feature_columns,
            "split_ratio": run.split_ratio,
            "confusion_matrices": {
                r.algorithm_name: r.confusion_matrix for r in run.results
            },
        }
    )
    return detail
