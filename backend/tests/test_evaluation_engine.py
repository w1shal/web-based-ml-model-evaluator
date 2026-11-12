from sklearn.datasets import load_iris
from sklearn.dummy import DummyClassifier
from app.ml.algorithms import BUILTIN_IDS
from app.ml.evaluator import EvaluationConfig, run_evaluation
from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm

def iris():
    frame = load_iris(as_frame=True).frame
    frame.columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "target"]
    return frame

def cfg(frame, algorithms):
    return EvaluationConfig("target", [c for c in frame.columns if c != "target"], algorithms)

def test_trains_and_evaluates_five_builtin_models():
    frame = iris()
    result = run_evaluation(frame, cfg(frame, list(BUILTIN_IDS)))
    assert result["status"] == "completed" and len(result["results"]) == 5
    assert all(row["status"] == "completed" for row in result["results"])
    assert result["dataset"]["rows"] == 150

def test_one_model_failure_does_not_stop_other_models():
    class Broken(DummyClassifier):
        def fit(self, X, y):
            raise RuntimeError("internal secret")
    register_algorithm(AlgorithmSpec("broken_algo", "Broken", lambda seed, rows: Broken()))
    try:
        result = run_evaluation(iris(), cfg(iris(), ["broken_algo", "decision_tree"]))
    finally:
        unregister_algorithm("broken_algo")
    assert result["status"] == "partial"
    assert result["results"][0]["status"] == "failed"
    assert "internal secret" not in result["results"][0]["error"]
    assert result["results"][1]["status"] == "completed"

def test_split_is_reproducible():
    frame = iris()
    one = run_evaluation(frame, cfg(frame, ["decision_tree"]))
    two = run_evaluation(frame, cfg(frame, ["decision_tree"]))
    assert one["results"][0]["accuracy"] == two["results"][0]["accuracy"]
