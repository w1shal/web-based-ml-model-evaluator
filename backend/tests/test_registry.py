import pytest
from sklearn.dummy import DummyClassifier

from app.ml.algorithms import BUILTIN_IDS
from app.ml.errors import EvaluationError
from app.ml.registry import AlgorithmSpec, get_algorithm, list_algorithms, register_algorithm, unregister_algorithm


def test_registry_contains_builtins_and_supports_custom_adapters():
    builtin_ids = set(BUILTIN_IDS)
    assert {item.id for item in list_algorithms()} == builtin_ids
    spec = AlgorithmSpec(id="stub_algo", name="Stub", factory=lambda seed, rows: DummyClassifier())
    register_algorithm(spec)
    try:
        assert get_algorithm("stub_algo") is spec
        with pytest.raises(ValueError):
            register_algorithm(spec)
    finally:
        unregister_algorithm("stub_algo")
    assert {item.id for item in list_algorithms()} == builtin_ids


def test_registry_rejects_invalid_ids_and_unknown_lookups():
    with pytest.raises(ValueError):
        register_algorithm(AlgorithmSpec(id="Bad Id", name="bad", factory=lambda seed, rows: None))
    with pytest.raises(EvaluationError) as exc:
        get_algorithm("missing_algo")
    assert exc.value.code == "UNKNOWN_ALGORITHM" and exc.value.status_code == 400
