"""Split, train and evaluate selected classifiers with ROC-AUC and confusion matrices."""
import logging
import math
import time
from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .errors import EvaluationError
from .metrics import classification_metrics, confusion_matrix_rows, roc_auc_metrics
from .preprocessing import build_preprocessor, prepare_data
from .selection import resolve_selection

log = logging.getLogger(__name__)
RANDOM_STATE = 42


@dataclass
class EvaluationConfig:
    target_column: str
    feature_columns: list[str]
    algorithms: list[str]
    test_size: float = 0.2
    missing_value_strategy: str = "median_imputation"
    random_state: int = RANDOM_STATE


def _decision_scores(model, X):
    """Get continuous scores for the encoded positive class (1)."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(X)
    return None


def run_evaluation(df: pd.DataFrame, cfg: EvaluationConfig) -> dict:
    if not 0.05 <= cfg.test_size <= 0.5:
        raise EvaluationError("INVALID_SPLIT", "test_size must be between 0.05 and 0.5", 400)
    specs = resolve_selection(cfg.algorithms)
    prepared = prepare_data(df, cfg.target_column, cfg.feature_columns, cfg.missing_value_strategy)
    n_classes = len(prepared.classes)
    n_test = math.ceil(cfg.test_size * len(prepared.y))
    if n_test < n_classes or len(prepared.y) - n_test < n_classes:
        raise EvaluationError("SPLIT_TOO_SMALL", "Not enough rows for a stratified train/test split", 422)
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            prepared.X, prepared.y, test_size=cfg.test_size,
            random_state=cfg.random_state, stratify=prepared.y)
    except ValueError:
        raise EvaluationError("SPLIT_FAILED", "Dataset cannot be stratified with this split", 422) from None
    results = []
    for spec in specs:
        started = time.perf_counter()
        try:
            model = Pipeline([
                ("preprocessor", build_preprocessor(prepared.numeric_cols, spec.needs_scaling)),
                ("classifier", spec.factory(cfg.random_state, len(y_train))),
            ])
            model.fit(X_train, y_train)
            predicted = model.predict(X_test)
            try:
                scores = _decision_scores(model, X_test) if n_classes == 2 else None
            except Exception:
                scores = None
            results.append({
                "algorithm": spec.id,
                "name": spec.name,
                "status": "completed",
                **classification_metrics(y_test, predicted, n_classes),
                **roc_auc_metrics(y_test, scores, n_classes),
                "confusion_matrix": confusion_matrix_rows(y_test, predicted, n_classes),
                "classes": prepared.classes,
                "duration_ms": int((time.perf_counter() - started) * 1000),
            })
        except Exception as exc:
            log.warning("Algorithm %s failed (%s)", spec.id, type(exc).__name__)
            results.append({
                "algorithm": spec.id,
                "name": spec.name,
                "status": "failed",
                "error": f"Training failed ({type(exc).__name__})",
                "duration_ms": int((time.perf_counter() - started) * 1000),
            })
    failed = sum(result["status"] == "failed" for result in results)
    status = "completed" if failed == 0 else "failed" if failed == len(results) else "partial"
    return {
        "status": status,
        "results": results,
        "dataset": {"rows": prepared.info["rows_used"], "train_rows": len(y_train), "test_rows": len(y_test)},
        "preprocessing": prepared.info,
    }
