import numpy as np
from sklearn.metrics import roc_auc_score

from app.ml.metrics import roc_auc_metrics


def test_binary_roc_auc_matches_sklearn():
    truth = np.array([0, 0, 1, 1, 0, 1])
    scores = np.array([0.05, 0.25, 0.8, 0.9, 0.4, 0.7])
    result = roc_auc_metrics(truth, scores, 2)
    assert result["roc_auc"] == roc_auc_score(truth, scores)
    assert result["roc_auc_applicable"] is True
    assert result["roc_auc_note"] is None


def test_multiclass_roc_auc_matches_sklearn_macro_ovr():
    truth = np.array([0, 1, 2, 0, 1, 2])
    scores = np.array([
        [0.7, 0.2, 0.1], [0.5, 0.4, 0.1], [0.1, 0.2, 0.7],
        [0.4, 0.5, 0.1], [0.2, 0.7, 0.1], [0.1, 0.1, 0.8],
    ])
    result = roc_auc_metrics(truth, scores, 3)
    assert np.isclose(result["roc_auc"], roc_auc_score(truth, scores, multi_class="ovr", average="macro"))
    assert result["roc_auc_note"] is None


def test_multiclass_roc_auc_requires_every_class_in_the_test_split():
    result = roc_auc_metrics(np.array([0, 1]), np.ones((2, 3)), 3)
    assert result["roc_auc"] is None
    assert result["roc_auc_note"]


def test_binary_roc_auc_handles_estimators_without_scores():
    result = roc_auc_metrics(np.array([0, 1]), None, 2)
    assert result["roc_auc"] is None
    assert result["roc_auc_applicable"] is True
    assert result["roc_auc_note"]
