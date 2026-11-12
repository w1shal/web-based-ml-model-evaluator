"""History persistence and query service (MLE-F-025/026/027).

The evaluation API should call persist_completed_evaluation() after its
evaluation engine has produced metrics. The authenticated user comes from the
verified JWT dependency; never accept a user_id from the request body.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import AlgorithmResult, EvaluationRun, User


def new_run_id() -> str:
    """Generate a collision-resistant run identifier."""
    return "run_" + uuid.uuid4().hex


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
    """Persist one completed evaluation.

    A None user_id represents a guest run. Guest records are not returned
    by list_runs(), which always filters on the authenticated user's ID.
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

    for result in results:
        serialized_metrics = result.get("serialized_metrics") or {}
        class_labels = result.get("class_labels") or result.get(
            "confusion_matrix_labels"
        )
        if class_labels is not None:
            serialized_metrics = {
                **serialized_metrics,
                "class_labels": list(class_labels),
            }

        run.results.append(
            AlgorithmResult(
                algorithm_name=result["algorithm"],
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                roc_auc=result.get("roc_auc"),
                confusion_matrix=result.get("confusion_matrix"),
                serialized_metrics=serialized_metrics or None,
            )
        )

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def persist_completed_evaluation(
    db: Session,
    authenticated_user: Optional[User],
    *,
    dataset_name: str,
    target_column: str,
    feature_columns: list,
    split_ratio: float,
    results: list[dict],
    timestamp: Optional[datetime] = None,
) -> EvaluationRun:
    """Persist a finished evaluator result using server-verified identity.

    The POST /evaluations handler (issue #43) should call this after evaluation:

        run = persist_completed_evaluation(
            db,
            current_user,  # User from get_optional_user(); None for guests
            dataset_name=dataset_name,
            target_column=target_column,
            feature_columns=feature_columns,
            split_ratio=split_ratio,
            results=results,
        )

    The user identity comes from the JWT dependency, not the request body.
    Guest results are stored with user_id=None and excluded from every
    authenticated user's history listing.
    """
    user_id = authenticated_user.user_id if authenticated_user else None
    return save_run(
        db,
        user_id,
        dataset_name=dataset_name,
        target_column=target_column,
        feature_columns=feature_columns,
        split_ratio=split_ratio,
        results=results,
        status="completed",
        timestamp=timestamp,
    )


def list_runs(db: Session, user_id: int, limit: int = 50, offset: int = 0):
    """Return only the caller's runs, newest first, with a stable tie-breaker."""
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
    """Delete the run and its AlgorithmResult rows using ORM cascade."""
    db.delete(run)
    db.commit()


def _metrics(result: AlgorithmResult) -> dict:
    metrics = {
        "algorithm": result.algorithm_name,
        "accuracy": result.accuracy,
        "precision": result.precision,
        "recall": result.recall,
        "f1_score": result.f1_score,
        "roc_auc": result.roc_auc,
    }
    metadata = result.serialized_metrics or {}
    labels = metadata.get("class_labels") or metadata.get(
        "confusion_matrix_labels"
    )
    if labels is not None:
        metrics["class_labels"] = labels
    return metrics


def _iso(timestamp: datetime) -> str:
    """Serialize naive UTC database timestamps with an explicit UTC suffix."""
    return timestamp.isoformat() + "Z"


def run_summary(run: EvaluationRun) -> dict:
    return {
        "run_id": run.run_id,
        "dataset_name": run.dataset_name,
        "timestamp": _iso(run.timestamp),
        "status": run.status,
        "algorithms": [result.algorithm_name for result in run.results],
        "metrics": [_metrics(result) for result in run.results],
    }


def run_detail(run: EvaluationRun) -> dict:
    detail = run_summary(run)
    detail.update(
        {
            "target_column": run.target_column,
            "feature_columns": run.feature_columns,
            "split_ratio": run.split_ratio,
            "confusion_matrices": {
                result.algorithm_name: result.confusion_matrix
                for result in run.results
            },
            "confusion_matrix_labels": {
                result.algorithm_name: (
                    (result.serialized_metrics or {}).get("class_labels")
                    or (result.serialized_metrics or {}).get(
                        "confusion_matrix_labels"
                    )
                )
                for result in run.results
            },
        }
    )
    return detail
