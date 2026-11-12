"""Classification metrics (MLE-F-017).

Averaging: binary for two classes (positive label is the second sorted class),
and support-weighted for three or more classes.
"""
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> dict:
    average = "binary" if n_classes == 2 else "weighted"
    kwargs = {"average": average, "zero_division": 0}
    if average == "binary":
        kwargs["pos_label"] = 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, **kwargs)),
        "recall": float(recall_score(y_true, y_pred, **kwargs)),
        "f1_score": float(f1_score(y_true, y_pred, **kwargs)),
        "metric_average": average,
    }
