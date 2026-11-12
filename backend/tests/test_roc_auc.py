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


def test_multiclass_roc_auc_is_explicitly_not_applicable():
    result = roc_auc_metrics(np.array([0, 1, 2]), None, 3)
    assert result == {
        "roc_auc": None,
        "roc_auc_applicable": False,
        "roc_auc_note": "ROC-AUC is only computed for binary classification.",
    }


def test_binary_roc_auc_handles_estimators_without_scores():
    result = roc_auc_metrics(np.array([0, 1]), None, 2)
    assert result["roc_auc"] is None
    assert result["roc_auc_applicable"] is True
    assert result["roc_auc_note"]
