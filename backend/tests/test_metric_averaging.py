import numpy as np
from sklearn.metrics import f1_score
from app.ml.metrics import classification_metrics

def test_binary_metrics_use_binary_average():
    truth = np.array([0, 0, 0, 1, 1])
    pred = np.array([0, 1, 0, 1, 0])
    metrics = classification_metrics(truth, pred, 2)
    assert metrics["metric_average"] == "binary"
    assert metrics["f1_score"] == f1_score(truth, pred, average="binary", pos_label=1)

def test_multiclass_metrics_use_weighted_average_on_imbalanced_labels():
    truth = np.array([0] * 70 + [1] * 20 + [2] * 10)
    pred = np.array([0] * 65 + [1] * 5 + [0] * 8 + [1] * 12 + [2] * 10)
    metrics = classification_metrics(truth, pred, 3)
    assert metrics["metric_average"] == "weighted"
    assert metrics["f1_score"] == f1_score(truth, pred, average="weighted", zero_division=0)
    assert abs(metrics["f1_score"] - f1_score(truth, pred, average="macro", zero_division=0)) > 1e-3
