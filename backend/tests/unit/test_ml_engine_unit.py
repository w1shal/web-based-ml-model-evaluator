"""Unit tests for the ML engine: preprocessing, metrics, evaluator, gate, registry, comparison."""

import threading

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

import app.ml  # noqa: F401  (registers the built-in algorithms)
from app.ml import evaluator as evaluator_module
from app.ml.comparison import compare
from app.ml.errors import EvaluationError
from app.ml.evaluator import EvaluationConfig, _decision_scores, run_evaluation
from app.ml.gate import EvaluationGate, GateTimeout
from app.ml.metrics import (
    ROC_AUC_NOT_APPLICABLE,
    ROC_AUC_UNAVAILABLE,
    classification_metrics,
    confusion_matrix_rows,
    roc_auc_metrics,
)
from app.ml.preprocessing import MAX_CATEGORIES_PER_FEATURE, build_preprocessor, prepare_data
from app.ml.registry import (
    AlgorithmSpec,
    get_algorithm,
    list_algorithms,
    register_algorithm,
    unregister_algorithm,
)
from app.ml.selection import MAX_ALGORITHMS_PER_RUN, resolve_selection

# ------------------------------------------------------------------ helpers


def binary_frame(rows: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    x1 = rng.normal(size=rows)
    return pd.DataFrame({
        "x1": x1,
        "x2": rng.normal(size=rows),
        "color": np.where(np.arange(rows) % 2 == 0, "red", "blue"),
        "label": (x1 > 0).astype(int),
    })


def config(**overrides) -> EvaluationConfig:
    values = {"target_column": "label", "feature_columns": ["x1", "x2"], "algorithms": ["decision_tree"]}
    values.update(overrides)
    return EvaluationConfig(**values)


class _ExplodingClassifier(ClassifierMixin, BaseEstimator):
    """Estimator stub whose fit always fails."""

    def fit(self, X, y):
        raise RuntimeError("boom")

    def predict(self, X):  # pragma: no cover - never reached
        return np.zeros(len(X))


class _NoScoreClassifier(ClassifierMixin, BaseEstimator):
    """Estimator stub with no predict_proba / decision_function."""

    def fit(self, X, y):
        self.label_ = int(np.bincount(y).argmax())
        return self

    def predict(self, X):
        return np.full(len(X), self.label_)


class _BrokenProbaClassifier(_NoScoreClassifier):
    def predict_proba(self, X):
        raise RuntimeError("scores unavailable")


@pytest.fixture
def temp_algorithm():
    """Register throwaway algorithms and always clean them up."""
    registered = []

    def _register(algorithm_id, factory):
        register_algorithm(AlgorithmSpec(algorithm_id, algorithm_id.title(), factory))
        registered.append(algorithm_id)
        return algorithm_id

    yield _register
    for algorithm_id in registered:
        unregister_algorithm(algorithm_id)


# ------------------------------------------------------------ preprocessing


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"strategy": "guess"}, "INVALID_STRATEGY"),
        ({"features": []}, "NO_FEATURES"),
        ({"features": ["x1", "x1"]}, "DUPLICATE_FEATURES"),
        ({"features": ["x1", "label"]}, "TARGET_IN_FEATURES"),
        ({"features": ["x1", "nope"]}, "UNKNOWN_COLUMN"),
        ({"target": "missing_target"}, "UNKNOWN_COLUMN"),
    ],
)
def test_prepare_data_rejects_invalid_requests(kwargs, code):
    args = {"target": "label", "features": ["x1", "x2"], "strategy": "median_imputation"}
    args.update(kwargs)
    with pytest.raises(EvaluationError) as error:
        prepare_data(binary_frame(), args["target"], args["features"], args["strategy"])
    assert error.value.code == code
    assert error.value.status_code == 400


def test_prepare_data_splits_numeric_and_categorical_columns():
    prepared = prepare_data(binary_frame(), "label", ["x1", "color"], "median_imputation")
    assert prepared.numeric_cols == ["x1"]
    assert prepared.categorical_cols == ["color"]
    assert prepared.classes == [0, 1]
    assert prepared.info["rows_total"] == prepared.info["rows_used"] == 40


def test_prepare_data_drops_rows_with_missing_target():
    frame = binary_frame()
    frame.loc[[0, 1], "label"] = np.nan
    prepared = prepare_data(frame, "label", ["x1"], "median_imputation")
    assert prepared.info["rows_total"] == 40
    assert prepared.info["rows_used"] == 38


def test_prepare_data_all_targets_missing_is_422():
    frame = binary_frame()
    frame["label"] = np.nan
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["x1"], "median_imputation")
    assert (error.value.code, error.value.status_code) == ("NO_USABLE_ROWS", 422)


def test_prepare_data_drop_rows_strategy_counts_dropped_rows():
    frame = binary_frame()
    frame.loc[[0, 1, 2], "x1"] = np.nan
    prepared = prepare_data(frame, "label", ["x1", "x2"], "drop_rows")
    assert prepared.info["rows_dropped_missing_features"] == 3
    assert prepared.info["rows_used"] == 37


def test_prepare_data_drop_rows_leaving_nothing_is_422():
    frame = binary_frame()
    frame["x1"] = np.nan
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["x1"], "drop_rows")
    assert error.value.code == "NO_USABLE_ROWS"


def test_prepare_data_converts_infinite_values_to_missing():
    frame = binary_frame()
    frame.loc[0, "x1"] = np.inf
    prepared = prepare_data(frame, "label", ["x1"], "median_imputation")
    assert np.isnan(prepared.X.loc[0, "x1"])


def test_prepare_data_rejects_too_many_categories():
    rows = (MAX_CATEGORIES_PER_FEATURE + 1) * 2
    frame = pd.DataFrame({
        "city": [f"c{i}" for i in range(rows)],
        "label": [i % 2 for i in range(rows)],
    })
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["city"], "median_imputation")
    assert error.value.code == "TOO_MANY_CATEGORIES"


def test_prepare_data_rejects_continuous_target():
    frame = binary_frame()
    frame["label"] = frame["x1"]
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["x2"], "median_imputation")
    assert error.value.code == "TARGET_NOT_DISCRETE"


def test_prepare_data_accepts_integral_float_target():
    frame = binary_frame()
    frame["label"] = frame["label"].astype(float)
    assert prepare_data(frame, "label", ["x1"], "median_imputation").classes == [0.0, 1.0]


def test_prepare_data_rejects_mixed_type_target():
    frame = binary_frame()
    frame["label"] = frame["label"].astype(object)
    frame.loc[0:5, "label"] = "text"
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["x1"], "median_imputation")
    assert error.value.code == "TARGET_MIXED_TYPES"


def test_prepare_data_rejects_single_class_and_tiny_classes():
    frame = binary_frame()
    frame["label"] = 1
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["x1"], "median_imputation")
    assert error.value.code == "TARGET_SINGLE_CLASS"

    frame["label"] = [0] + [1] * 39
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "label", ["x1"], "median_imputation")
    assert error.value.code == "CLASS_TOO_SMALL"


@pytest.mark.parametrize(
    ("numeric", "categorical", "scale", "expected"),
    [
        (["x1"], [], False, ["numeric"]),
        ([], ["color"], False, ["categorical"]),
        (["x1"], ["color"], True, ["numeric", "categorical"]),
    ],
)
def test_build_preprocessor_includes_needed_transformers(numeric, categorical, scale, expected):
    transformer = build_preprocessor(numeric, categorical, scale)
    assert [name for name, _, _ in transformer.transformers] == expected
    if numeric:
        steps = dict(transformer.transformers[0][1].steps)
        assert ("scale" in steps) is scale


# ----------------------------------------------------------------- metrics


def test_classification_metrics_binary_and_weighted():
    binary = classification_metrics(np.array([0, 1, 1, 0]), np.array([0, 1, 0, 0]), 2)
    assert binary["metric_average"] == "binary"
    assert binary["accuracy"] == pytest.approx(0.75)
    assert binary["precision"] == pytest.approx(1.0)
    assert binary["recall"] == pytest.approx(0.5)

    multi = classification_metrics(np.array([0, 1, 2]), np.array([0, 1, 2]), 3)
    assert multi["metric_average"] == "weighted"
    assert multi["f1_score"] == pytest.approx(1.0)


def test_confusion_matrix_rows_includes_unpredicted_labels():
    assert confusion_matrix_rows(np.array([0, 0, 1]), np.array([0, 0, 0]), 3) == [
        [2, 0, 0], [1, 0, 0], [0, 0, 0],
    ]


def test_roc_auc_metrics_branches():
    y = np.array([0, 0, 1, 1])
    assert roc_auc_metrics(y, None, 3)["roc_auc_note"] == ROC_AUC_NOT_APPLICABLE
    assert roc_auc_metrics(y, None, 2)["roc_auc_note"] == ROC_AUC_UNAVAILABLE
    assert roc_auc_metrics(y, np.array([0.1, 0.2, 0.8, 0.9]), 2)["roc_auc"] == pytest.approx(1.0)
    # Mismatched lengths make sklearn raise ValueError, which must be handled.
    broken = roc_auc_metrics(y, np.array([0.1, 0.2]), 2)
    assert broken["roc_auc"] is None and broken["roc_auc_applicable"] is True


# --------------------------------------------------------------- evaluator


def test_decision_scores_prefers_probabilities_then_decision_function():
    X = np.array([[0.0], [1.0], [2.0], [3.0]])
    y = np.array([0, 0, 1, 1])
    tree = DecisionTreeClassifier(random_state=0).fit(X, y)
    assert _decision_scores(tree, X).shape == (4,)
    svc = SVC().fit(X, y)  # no probability=True -> decision_function only
    assert np.allclose(_decision_scores(svc, X), svc.decision_function(X))
    assert _decision_scores(_NoScoreClassifier().fit(X, y), X) is None


@pytest.mark.parametrize("test_size", [0.01, 0.6])
def test_run_evaluation_rejects_out_of_range_split(test_size):
    with pytest.raises(EvaluationError) as error:
        run_evaluation(binary_frame(), config(test_size=test_size))
    assert error.value.code == "INVALID_SPLIT"


def test_run_evaluation_rejects_split_too_small_for_classes():
    frame = pd.DataFrame({"x1": range(6), "label": [0, 0, 1, 1, 2, 2]})
    with pytest.raises(EvaluationError) as error:
        run_evaluation(frame, config(feature_columns=["x1"], test_size=0.2))
    assert error.value.code == "SPLIT_TOO_SMALL"


def test_run_evaluation_maps_stratify_failure(monkeypatch):
    def failing_split(*args, **kwargs):
        raise ValueError("cannot stratify")

    monkeypatch.setattr(evaluator_module, "train_test_split", failing_split)
    with pytest.raises(EvaluationError) as error:
        run_evaluation(binary_frame(), config())
    assert (error.value.code, error.value.status_code) == ("SPLIT_FAILED", 422)


def test_run_evaluation_success_payload():
    outcome = run_evaluation(binary_frame(), config(algorithms=["decision_tree", "svm"]))
    assert outcome["status"] == "completed"
    assert outcome["dataset"] == {"rows": 40, "train_rows": 32, "test_rows": 8}
    for result in outcome["results"]:
        assert result["status"] == "completed"
        assert 0.0 <= result["accuracy"] <= 1.0
        assert result["roc_auc_applicable"] is True
        assert result["classes"] == [0, 1]
        assert sum(map(sum, result["confusion_matrix"])) == 8


def test_run_evaluation_is_deterministic():
    first = run_evaluation(binary_frame(), config(algorithms=["random_forest"]))
    second = run_evaluation(binary_frame(), config(algorithms=["random_forest"]))
    keys = ("accuracy", "precision", "recall", "f1_score", "roc_auc", "confusion_matrix")
    assert {k: first["results"][0][k] for k in keys} == {k: second["results"][0][k] for k in keys}


def test_run_evaluation_reports_partial_and_failed_runs(temp_algorithm):
    exploding = temp_algorithm("exploding_test", lambda seed, rows: _ExplodingClassifier())

    partial = run_evaluation(binary_frame(), config(algorithms=["decision_tree", exploding]))
    assert partial["status"] == "partial"
    failed_row = partial["results"][1]
    assert failed_row["status"] == "failed"
    assert failed_row["error"] == "Training failed (RuntimeError)"
    assert "accuracy" not in failed_row

    failed = run_evaluation(binary_frame(), config(algorithms=[exploding]))
    assert failed["status"] == "failed"


def test_run_evaluation_handles_missing_or_broken_scores(temp_algorithm):
    no_scores = temp_algorithm("no_scores_test", lambda seed, rows: _NoScoreClassifier())
    broken = temp_algorithm("broken_proba_test", lambda seed, rows: _BrokenProbaClassifier())
    outcome = run_evaluation(binary_frame(), config(algorithms=[no_scores, broken]))
    assert outcome["status"] == "completed"
    for result in outcome["results"]:
        assert result["roc_auc"] is None
        assert result["roc_auc_note"] == ROC_AUC_UNAVAILABLE


def test_run_evaluation_multiclass_has_no_roc_auc():
    frame = pd.DataFrame({"x1": np.arange(30, dtype=float), "label": np.repeat([0, 1, 2], 10)})
    outcome = run_evaluation(frame, config(feature_columns=["x1"], algorithms=["knn"], test_size=0.3))
    result = outcome["results"][0]
    assert result["roc_auc"] is None
    assert result["roc_auc_applicable"] is False
    assert result["metric_average"] == "weighted"
    assert len(result["confusion_matrix"]) == 3


# --------------------------------------------------------------------- gate


@pytest.mark.parametrize(("slots", "timeout"), [(0, 1), (-1, 1), (1, -0.5)])
def test_gate_rejects_invalid_configuration(slots, timeout):
    with pytest.raises(ValueError):
        EvaluationGate(slots, timeout)


def test_gate_tracks_running_and_peak():
    gate = EvaluationGate(2, 1)
    with gate.slot(), gate.slot():
        assert gate.stats()["running"] == 2
    assert gate.stats() == {"running": 0, "waiting": 0, "max_concurrent": 2, "peak_running": 2}


def test_gate_times_out_when_full():
    gate = EvaluationGate(1, 0.05)
    holding, release = threading.Event(), threading.Event()

    def hold():
        with gate.slot():
            holding.set()
            release.wait(5)

    worker = threading.Thread(target=hold)
    worker.start()
    try:
        assert holding.wait(5)
        with pytest.raises(GateTimeout), gate.slot():
            pass  # pragma: no cover
        assert gate.stats()["waiting"] == 0
    finally:
        release.set()
        worker.join(5)
    with gate.slot():  # slot is free again after release
        assert gate.stats()["running"] == 1


def test_gate_releases_slot_when_body_raises():
    gate = EvaluationGate(1, 0)
    with pytest.raises(RuntimeError), gate.slot():
        raise RuntimeError("failure inside evaluation")
    assert gate.stats()["running"] == 0
    with gate.slot():
        pass


# --------------------------------------------------- registry / selection


def test_registry_rejects_invalid_and_duplicate_ids(temp_algorithm):
    with pytest.raises(ValueError, match="Invalid"):
        register_algorithm(AlgorithmSpec("Bad-ID", "Bad", lambda s, r: None))
    algorithm_id = temp_algorithm("dup_test", lambda s, r: None)
    with pytest.raises(ValueError, match="already registered"):
        register_algorithm(AlgorithmSpec(algorithm_id, "Dup", lambda s, r: None))
    replacement = AlgorithmSpec(algorithm_id, "Replaced", lambda s, r: None)
    register_algorithm(replacement, replace=True)
    assert get_algorithm(algorithm_id).name == "Replaced"


def test_registry_lookup_and_unregister(temp_algorithm):
    algorithm_id = temp_algorithm("lookup_test", lambda s, r: None)
    assert algorithm_id in {spec.id for spec in list_algorithms()}
    unregister_algorithm(algorithm_id)
    unregister_algorithm(algorithm_id)  # idempotent
    with pytest.raises(EvaluationError) as error:
        get_algorithm(algorithm_id)
    assert error.value.code == "UNKNOWN_ALGORITHM"


def test_selection_deduplicates_and_limits():
    specs = resolve_selection(["knn", "svm", "knn"])
    assert [spec.id for spec in specs] == ["knn", "svm"]
    with pytest.raises(EvaluationError) as error:
        resolve_selection([])
    assert error.value.code == "NO_ALGORITHM"
    too_many = [f"a{i}x" for i in range(MAX_ALGORITHMS_PER_RUN + 1)]
    with pytest.raises(EvaluationError) as error:
        resolve_selection(too_many)
    assert error.value.code == "TOO_MANY_ALGORITHMS"


# --------------------------------------------------------------- comparison


def test_compare_ranks_by_metric_then_accuracy_then_name():
    results = [
        {"algorithm": "b", "status": "completed", "f1_score": 0.8, "accuracy": 0.7, "roc_auc": None},
        {"algorithm": "a", "status": "completed", "f1_score": 0.8, "accuracy": 0.7, "roc_auc": 0.9},
        {"algorithm": "c", "status": "completed", "f1_score": 0.8, "accuracy": 0.9, "roc_auc": 0.5},
        {"algorithm": "d", "status": "failed"},
    ]
    summary = compare(results)
    assert [row["algorithm"] for row in summary["ranking"]] == ["c", "a", "b"]
    assert [row["rank"] for row in summary["ranking"]] == [1, 2, 3]
    assert summary["best_by_metric"]["roc_auc"] == "a"
    assert summary["best_by_metric"]["accuracy"] == "c"
    assert "precision" not in summary["best_by_metric"]


def test_compare_with_no_completed_results():
    assert compare([{"algorithm": "x", "status": "failed"}]) == {
        "ranking_metric": "f1_score", "ranking": [], "best_by_metric": {},
    }
