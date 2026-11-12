"""Reference-compatible classification metrics and confusion matrices."""
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score


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


def confusion_matrix_rows(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> list[list[int]]:
    """Return matrix rows as true labels and columns as predicted labels."""
    return confusion_matrix(y_true, y_pred, labels=list(range(n_classes))).tolist()
