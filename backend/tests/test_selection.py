import pytest
from sklearn.dummy import DummyClassifier

from app.ml.errors import EvaluationError
from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm
from app.ml.selection import resolve_selection

def test_selection_preserves_order_and_removes_duplicates():
    for name in ("one_algo", "two_algo"):
        register_algorithm(AlgorithmSpec(name, name, lambda seed, rows: DummyClassifier()))
    try:
        assert [item.id for item in resolve_selection(["two_algo", "one_algo", "two_algo"])] == ["two_algo", "one_algo"]
    finally:
        unregister_algorithm("one_algo")
        unregister_algorithm("two_algo")

def test_selection_rejects_empty_unknown_and_more_than_five():
    with pytest.raises(EvaluationError) as exc:
        resolve_selection([])
    assert exc.value.code == "NO_ALGORITHM"
    with pytest.raises(EvaluationError) as exc:
        resolve_selection(["unknown_algo"])
    assert exc.value.code == "UNKNOWN_ALGORITHM"
    ids = [f"stub_{index}" for index in range(6)]
    for name in ids:
        register_algorithm(AlgorithmSpec(name, name, lambda seed, rows: DummyClassifier()))
    try:
        with pytest.raises(EvaluationError) as exc:
            resolve_selection(ids)
        assert exc.value.code == "TOO_MANY_ALGORITHMS"
    finally:
        for name in ids:
            unregister_algorithm(name)
