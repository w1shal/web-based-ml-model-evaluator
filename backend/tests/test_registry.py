import pytest
from sklearn.dummy import DummyClassifier

from app.ml.algorithms import BUILTIN_IDS
from app.ml.errors import EvaluationError
from app.ml.registry import AlgorithmSpec, get_algorithm, list_algorithms, register_algorithm, unregister_algorithm


def test_exactly_five_builtin_algorithms():
    ids = [algorithm.id for algorithm in list_algorithms()]
    assert ids == list(BUILTIN_IDS)
    assert set(ids) == {"logistic_regression", "decision_tree", "random_forest", "svm", "knn"}


def test_algorithms_endpoint_lists_five(client):
    response = client.get("/algorithms")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == list(BUILTIN_IDS)


@pytest.mark.parametrize("algorithm_id", BUILTIN_IDS)
def test_every_factory_builds_a_working_estimator(algorithm_id):
    estimator = get_algorithm(algorithm_id).factory(42, 100)
    assert hasattr(estimator, "fit") and hasattr(estimator, "predict")


def test_unknown_algorithm_rejected():
    with pytest.raises(EvaluationError) as exc:
        get_algorithm("neural_net")
    assert exc.value.status_code == 400 and exc.value.code == "UNKNOWN_ALGORITHM"


def test_register_validates_and_rejects_duplicates():
    spec = AlgorithmSpec(id="stub_algo", name="Stub", factory=lambda seed, rows: DummyClassifier())
    register_algorithm(spec)
    try:
        assert "stub_algo" in [algorithm.id for algorithm in list_algorithms()]
        with pytest.raises(ValueError):
            register_algorithm(spec)
        with pytest.raises(ValueError):
            register_algorithm(AlgorithmSpec(id="Bad Id!", name="x", factory=lambda seed, rows: None))
    finally:
        unregister_algorithm("stub_algo")
