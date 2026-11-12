import pytest
from app.ml.errors import EvaluationError
from app.ml.selection import select_algorithms


def test_selection_preserves_order_and_removes_duplicates():
    assert [item.id for item in select_algorithms(["knn", "svm", "knn"])] == ["knn", "svm"]


def test_selection_rejects_empty_and_unknown_ids():
    with pytest.raises(EvaluationError) as empty:
        select_algorithms([])
    assert empty.value.code == "NO_ALGORITHM"
    with pytest.raises(EvaluationError) as unknown:
        select_algorithms(["not_registered"])
    assert unknown.value.code == "UNKNOWN_ALGORITHM"


def test_selection_rejects_more_than_five_distinct_algorithms():
    with pytest.raises(EvaluationError) as error:
        select_algorithms(["logistic_regression", "decision_tree", "random_forest", "svm", "knn", "another"])
    assert error.value.code == "TOO_MANY_ALGORITHMS"
