"""Evaluation orchestrator: split, train registered models and calculate metrics."""
import logging
import math
import time
from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .errors import EvaluationError
from .metrics import classification_metrics
from .preprocessing import build_preprocessor, prepare_data
from .selection import select_algorithms

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


def run_evaluation(df: pd.DataFrame, cfg: EvaluationConfig) -> dict:
    specs = select_algorithms(cfg.algorithms)
    if not 0 < cfg.test_size < 1:
        raise EvaluationError("INVALID_SPLIT", "test_size must be between 0 and 1", 400)
    prep = prepare_data(df, cfg.target_column, cfg.feature_columns, cfg.missing_value_strategy)
    n, n_classes = len(prep.y), len(prep.classes)
    n_test = math.ceil(cfg.test_size * n)
    if n_test < n_classes or n - n_test < n_classes:
        raise EvaluationError("SPLIT_TOO_SMALL", "Too few rows for this split: each class needs rows in both the training and test sets", 422)
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            prep.X, prep.y, test_size=cfg.test_size, random_state=cfg.random_state, stratify=prep.y)
    except ValueError:
        raise EvaluationError("SPLIT_FAILED", "The dataset cannot be split with these settings", 422)
    results = []
    for spec in specs:
        started = time.perf_counter()
        try:
            model = Pipeline([
                ("prep", build_preprocessor(prep.numeric_cols, spec.needs_scaling)),
                ("model", spec.factory(cfg.random_state, len(y_train))),
            ])
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            results.append({"algorithm": spec.id, "name": spec.name, "status": "completed",
                            **classification_metrics(y_test, y_pred, n_classes),
                            "duration_ms": int((time.perf_counter() - started) * 1000)})
        except Exception as exc:
            log.warning("algorithm %s failed: %s", spec.id, type(exc).__name__)
            results.append({"algorithm": spec.id, "name": spec.name, "status": "failed",
                            "error": f"Training failed ({type(exc).__name__})",
                            "duration_ms": int((time.perf_counter() - started) * 1000)})
    failed = sum(result["status"] == "failed" for result in results)
    status = "completed" if failed == 0 else ("failed" if failed == len(results) else "partial")
    return {"status": status, "results": results,
            "dataset": {"rows": prep.info["rows_used"], "train_rows": int(len(y_train)), "test_rows": int(len(y_test))},
            "preprocessing": prep.info}
