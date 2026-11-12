import pytest
from sklearn.dummy import DummyClassifier

from app.ml.errors import EvaluationError
from app.ml.registry import AlgorithmSpec, get_algorithm, list_algorithms, register_algorithm, unregister_algorithm


def test_registry_register_get_list_and_unregister():
    spec = AlgorithmSpec(id="stub_algo", name="Stub", factory=lambda seed, rows: DummyClassifier())
    register_algorithm(spec)
    try:
        assert get_algorithm("stub_algo") == spec
        assert spec in list_algorithms()
    finally:
        unregister_algorithm("stub_algo")
    assert all(item.id != "stub_algo" for item in list_algorithms())


def test_registry_rejects_duplicate_and_invalid_ids():
    spec = AlgorithmSpec(id="stub_algo", name="Stub", factory=lambda seed, rows: DummyClassifier())
    register_algorithm(spec)
    try:
        with pytest.raises(ValueError):
            register_algorithm(spec)
    finally:
        unregister_algorithm("stub_algo")
    with pytest.raises(ValueError):
        register_algorithm(AlgorithmSpec(id="Bad Id!", name="Bad", factory=lambda seed, rows: None))


def test_unknown_algorithm_raises_controlled_error():
    with pytest.raises(EvaluationError) as error:
        get_algorithm("not_registered")
    assert error.value.code == "UNKNOWN_ALGORITHM"
    assert error.value.status_code == 400
