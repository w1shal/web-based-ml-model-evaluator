from app.ml.algorithms import BUILTIN_IDS
from app.ml.registry import get_algorithm, list_algorithms

def test_five_required_classifiers_are_registered():
    assert tuple(item.id for item in list_algorithms()) == BUILTIN_IDS
    assert set(BUILTIN_IDS) == {"logistic_regression", "decision_tree", "random_forest", "svm", "knn"}

def test_each_builtin_factory_returns_a_classifier():
    for algorithm_id in BUILTIN_IDS:
        estimator = get_algorithm(algorithm_id).factory(42, 100)
        assert callable(estimator.fit) and callable(estimator.predict)
