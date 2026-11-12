"""Evaluation use case: load, execute, persist and retrieve evaluations."""
from typing import Optional

from sqlalchemy.orm import Session

from ..ml.comparison import compare
from ..ml.errors import EvaluationError
from ..ml.evaluator import EvaluationConfig, run_evaluation
from ..ml.gate import GateTimeout, evaluation_gate
from ..models import EvaluationRun
from ..schemas_evaluation import EvaluationRequest
from . import dataset_store
from .history import save_run

_DONE_KEYS = ("accuracy", "precision", "recall", "f1_score", "roc_auc", "confusion_matrix")
_EXTRA_KEYS = ("name", "status", "error", "duration_ms", "metric_average", "classes", "class_labels",
               "roc_auc_applicable", "roc_auc_note")


def _to_history_row(result: dict, run_info: dict) -> dict:
    row = {key: result.get(key) for key in _DONE_KEYS}
    row["algorithm"] = result["algorithm"]
    metadata = {key: result[key] for key in _EXTRA_KEYS if key in result}
    if "classes" in metadata and "class_labels" not in metadata:
        metadata["class_labels"] = metadata["classes"]
    row["serialized_metrics"] = {**metadata, "run_info": run_info}
    return row


def _from_history_row(row) -> dict:
    extras = dict(row.serialized_metrics or {})
    extras.pop("run_info", None)
    labels = extras.pop("class_labels", None)
    if "classes" not in extras and labels is not None:
        extras["classes"] = labels
    result = {"algorithm": row.algorithm_name, **extras}
    if extras.get("status", "completed") == "completed":
        result.update({key: getattr(row, key) for key in _DONE_KEYS})
    return result


def _response(run_id: str, status: str, dataset: dict, results: list[dict], preprocessing: dict) -> dict:
    return {"run_id": run_id, "status": status, "dataset": dataset, "results": results,
            "comparison": compare(results), "preprocessing": preprocessing}


def execute_evaluation(db: Session, user_id: Optional[int], request: EvaluationRequest) -> dict:
    dataset = dataset_store.load_dataset(request.dataset_id, user_id)
    db.rollback()
    config = EvaluationConfig(
        target_column=request.target_column,
        feature_columns=request.feature_columns,
        algorithms=request.algorithms,
        test_size=request.test_size,
        missing_value_strategy=request.missing_value_strategy,
    )
    try:
        with evaluation_gate.slot():
            outcome = run_evaluation(dataset.df, config)
    except GateTimeout:
        raise EvaluationError("SERVER_BUSY", "The server is busy. Please try again shortly.", 503)

    run_info = {"dataset": outcome["dataset"], "preprocessing": outcome["preprocessing"]}
    run = save_run(
        db, user_id, dataset_name=dataset.name, target_column=request.target_column,
        feature_columns=request.feature_columns, split_ratio=request.test_size, status=outcome["status"],
        results=[_to_history_row(result, run_info) for result in outcome["results"]],
    )
    return _response(run.run_id, outcome["status"], {"name": dataset.name, **outcome["dataset"]},
                     outcome["results"], outcome["preprocessing"])


def get_evaluation(db: Session, run_id: str, user_id: Optional[int]) -> dict:
    run = db.get(EvaluationRun, run_id)
    if run is None:
        raise EvaluationError("RUN_NOT_FOUND", "Run not found", 404)
    if run.user_id is not None:
        if user_id is None:
            raise EvaluationError("AUTH_REQUIRED", "Authentication required", 401)
        if run.user_id != user_id:
            raise EvaluationError("FORBIDDEN", "You do not have access to this run", 403)
    results = [_from_history_row(row) for row in run.results]
    run_info = (run.results[0].serialized_metrics or {}).get("run_info", {}) if run.results else {}
    return _response(run.run_id, run.status, {"name": run.dataset_name, **run_info.get("dataset", {})},
                     results, run_info.get("preprocessing", {}))
