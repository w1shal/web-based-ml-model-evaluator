"""Core classification metrics."""
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> dict:
    average = "binary" if n_classes == 2 else "weighted"
    params = {"average": average, "zero_division": 0}
    if average == "binary":
        params["pos_label"] = 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, **params)),
        "recall": float(recall_score(y_true, y_pred, **params)),
        "f1_score": float(f1_score(y_true, y_pred, **params)),
    }
