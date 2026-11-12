import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from app.ml.algorithms import BUILTIN_IDS
from app.ml.errors import EvaluationError
from app.ml.evaluator import EvaluationConfig, run_evaluation
from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm
from tests.ml_helpers import cancer_df, features_of, iris_df, synthetic_df


def cfg(frame, target, algorithms, **kwargs):
    return EvaluationConfig(target_column=target, feature_columns=features_of(frame, target),
                            algorithms=list(algorithms), **kwargs)


def by_algorithm(outcome):
    return {result["algorithm"]: result for result in outcome["results"]}


def test_all_five_algorithms_run_end_to_end():
    frame = cancer_df()
    outcome = run_evaluation(frame, cfg(frame, "diagnosis", BUILTIN_IDS))
    assert outcome["status"] == "completed" and len(outcome["results"]) == 5
    assert all(result["status"] == "completed" for result in outcome["results"])
    assert outcome["dataset"] == {"rows": 569, "train_rows": 455, "test_rows": 114}


@pytest.mark.parametrize("count", [1, 3, 5])
def test_multi_select_runs_exactly_the_selected(count):
    frame = iris_df()
    selected = list(BUILTIN_IDS)[:count]
    outcome = run_evaluation(frame, cfg(frame, "species", selected))
    assert [result["algorithm"] for result in outcome["results"]] == selected


def test_duplicate_algorithm_ids_run_once():
    frame = iris_df()
    outcome = run_evaluation(frame, cfg(frame, "species", ["knn", "knn", "svm"]))
    assert [result["algorithm"] for result in outcome["results"]] == ["knn", "svm"]


def test_empty_and_unknown_algorithm_lists_are_rejected():
    frame = iris_df()
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(frame, cfg(frame, "species", []))
    assert exc.value.status_code == 400
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(frame, cfg(frame, "species", ["knn", "magic"]))
    assert exc.value.code == "UNKNOWN_ALGORITHM"


def test_more_than_five_distinct_registered_algorithms_are_rejected():
    frame = iris_df()
    extra = AlgorithmSpec(id="stub_algo", name="Stub", factory=lambda seed, rows: DummyClassifier())
    register_algorithm(extra)
    try:
        with pytest.raises(EvaluationError) as exc:
            run_evaluation(frame, cfg(frame, "species", [*BUILTIN_IDS, "stub_algo"]))
        assert exc.value.code == "TOO_MANY_ALGORITHMS" and exc.value.status_code == 400
    finally:
        unregister_algorithm("stub_algo")


def test_tree_metrics_match_independent_scikit_learn_reference():
    frame = iris_df()
    results = by_algorithm(run_evaluation(frame, cfg(frame, "species", ["decision_tree", "random_forest"])))
    X, y = frame[features_of(frame, "species")], frame["species"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    references = {
        "decision_tree": DecisionTreeClassifier(random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1),
    }
    for algorithm, model in references.items():
        predicted = model.fit(X_train, y_train).predict(X_test)
        result = results[algorithm]
        assert result["accuracy"] == pytest.approx(accuracy_score(y_test, predicted), abs=1e-6)
        assert result["precision"] == pytest.approx(precision_score(y_test, predicted, average="weighted", zero_division=0), abs=1e-6)
        assert result["recall"] == pytest.approx(recall_score(y_test, predicted, average="weighted", zero_division=0), abs=1e-6)
        assert result["f1_score"] == pytest.approx(f1_score(y_test, predicted, average="weighted", zero_division=0), abs=1e-6)


def test_metric_averaging_is_reported():
    multi = run_evaluation(iris_df(), cfg(iris_df(), "species", BUILTIN_IDS))
    binary = run_evaluation(cancer_df(), cfg(cancer_df(), "diagnosis", BUILTIN_IDS))
    assert {result["metric_average"] for result in multi["results"]} == {"weighted"}
    assert {result["metric_average"] for result in binary["results"]} == {"binary"}


def test_identical_configuration_gives_deterministic_metrics():
    frame = cancer_df()
    first = run_evaluation(frame, cfg(frame, "diagnosis", BUILTIN_IDS))
    second = run_evaluation(frame, cfg(frame, "diagnosis", BUILTIN_IDS))
    strip = lambda output: [{key: value for key, value in result.items() if key != "duration_ms"} for result in output["results"]]
    assert strip(first) == strip(second)


def test_scale_sensitive_algorithms_handle_different_feature_scales():
    frame = synthetic_df(300, 4)
    frame["f0"] *= 1e6
    frame["f1"] *= 1e-4
    results = by_algorithm(run_evaluation(frame, cfg(frame, "label", ["knn", "svm", "logistic_regression"])))
    assert all(result["status"] == "completed" for result in results.values())
    assert min(result["accuracy"] for result in results.values()) > 0.7


def test_single_class_and_tiny_classes_give_controlled_errors():
    frame = iris_df()
    one_class = frame.assign(species=0)
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(one_class, cfg(one_class, "species", ["knn"]))
    assert exc.value.status_code == 422 and exc.value.code == "TARGET_SINGLE_CLASS"
    tiny = pd.DataFrame({"a": [1.0, 2.0, 3.0], "y": ["x", "y", "z"]})
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(tiny, cfg(tiny, "y", ["knn"]))
    assert exc.value.status_code == 422 and exc.value.code == "CLASS_TOO_SMALL"


def test_target_in_features_and_unknown_columns_are_rejected():
    frame = iris_df()
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(frame, EvaluationConfig("species", ["species", "petal_width"], ["knn"]))
    assert exc.value.code == "TARGET_IN_FEATURES"
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(frame, EvaluationConfig("species", ["not_a_column"], ["knn"]))
    assert exc.value.code == "UNKNOWN_COLUMN"


def test_continuous_target_and_invalid_strategy_are_rejected():
    frame = pd.DataFrame({"feature": np.arange(50.0), "target": np.linspace(0.1, 9.9, 50)})
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(frame, EvaluationConfig("target", ["feature"], ["knn"]))
    assert exc.value.code == "TARGET_NOT_DISCRETE"
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(iris_df(), EvaluationConfig("species", ["petal_width"], ["knn"], missing_value_strategy="guess"))
    assert exc.value.code == "INVALID_STRATEGY"


def test_one_algorithm_failure_does_not_stop_other_algorithms():
    class Boom(DummyClassifier):
        def fit(self, X, y, *args, **kwargs):
            raise RuntimeError("private internal detail")

    register_algorithm(AlgorithmSpec(id="boom_algo", name="Boom", factory=lambda seed, rows: Boom()))
    try:
        frame = iris_df()
        combined = run_evaluation(frame, cfg(frame, "species", ["boom_algo", "decision_tree"]))
        alone = run_evaluation(frame, cfg(frame, "species", ["decision_tree"]))
    finally:
        unregister_algorithm("boom_algo")
    assert combined["status"] == "partial"
    by_id = by_algorithm(combined)
    assert by_id["boom_algo"]["status"] == "failed"
    assert "private internal detail" not in by_id["boom_algo"]["error"]
    strip = lambda result: {key: value for key, value in result.items() if key != "duration_ms"}
    assert strip(by_id["decision_tree"]) == strip(alone["results"][0])
