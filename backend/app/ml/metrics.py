"""Classification metrics, confusion matrices and binary ROC-AUC."""
from typing import Optional

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

ROC_AUC_NOT_APPLICABLE = "ROC-AUC is only computed for binary classification (2 classes)"
ROC_AUC_FAILED = "ROC-AUC could not be computed for this model"


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


def confusion_matrix_rows(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> list[list[int]]:
    """Rows are true classes and columns are predicted classes in sorted label order."""
    return confusion_matrix(y_true, y_pred, labels=list(range(n_classes))).tolist()


def roc_auc(y_true: np.ndarray, scores: Optional[np.ndarray], n_classes: int) -> dict:
    if n_classes != 2:
        return {"roc_auc": None, "roc_auc_applicable": False, "roc_auc_note": ROC_AUC_NOT_APPLICABLE}
    try:
        if scores is None:
            raise ValueError("Model does not expose a decision score")
        return {"roc_auc": float(roc_auc_score(y_true, scores)), "roc_auc_applicable": True, "roc_auc_note": None}
    except Exception:
        return {"roc_auc": None, "roc_auc_applicable": True, "roc_auc_note": ROC_AUC_FAILED}
