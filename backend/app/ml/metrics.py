"""Reference-compatible classification metrics.

A two-class target uses binary averaging (the second sorted/encoded class is
positive). Multiclass targets use support-weighted averaging, not macro.
"""
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> dict:
    average = "binary" if n_classes == 2 else "weighted"
    options = {"average": average, "zero_division": 0}
    if average == "binary":
        options["pos_label"] = 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, **options)),
        "recall": float(recall_score(y_true, y_pred, **options)),
        "f1_score": float(f1_score(y_true, y_pred, **options)),
        "metric_average": average,
    }
