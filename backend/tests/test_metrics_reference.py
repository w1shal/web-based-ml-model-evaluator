import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import load_breast_cancer, load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from app.ml.algorithms import BUILTIN_IDS
from app.ml.evaluator import EvaluationConfig, run_evaluation
from app.ml.metrics import ROC_AUC_NOT_APPLICABLE

TOLERANCE = 1e-6
REFERENCE_MODELS = {
    "logistic_regression": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=42)),
    "decision_tree": lambda: DecisionTreeClassifier(random_state=42),
    "random_forest": lambda: RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1),
    "svm": lambda: make_pipeline(StandardScaler(), SVC(kernel="rbf", random_state=42)),
    "knn": lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
}


def breast_cancer_frame():
    data = load_breast_cancer(as_frame=True)
    frame = data.data.copy()
    frame["diagnosis"] = data.target
    return frame


def iris_frame():
    data = load_iris(as_frame=True)
    frame = data.data.copy()
    frame["species"] = data.target
    return frame


def run_all(frame, target):
    features = [column for column in frame.columns if column != target]
    outcome = run_evaluation(frame, EvaluationConfig(target, features, list(BUILTIN_IDS)))
    return {row["algorithm"]: row for row in outcome["results"]}


def reference(frame, target, algorithm):
    features = [column for column in frame.columns if column != target]
    x, y = frame[features], frame[target]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y)
    model = REFERENCE_MODELS[algorithm]().fit(x_train, y_train)
    return y_test, model.predict(x_test), model, x_test


@pytest.mark.parametrize("algorithm", BUILTIN_IDS)
def test_binary_metrics_confusion_and_auc_match_sklearn(algorithm):
    frame = breast_cancer_frame()
    result = run_all(frame, "diagnosis")[algorithm]
    y_test, prediction, model, x_test = reference(frame, "diagnosis", algorithm)
    scores = model.decision_function(x_test) if algorithm == "svm" else model.predict_proba(x_test)[:, 1]
    assert result["accuracy"] == pytest.approx(accuracy_score(y_test, prediction), abs=TOLERANCE)
    assert result["precision"] == pytest.approx(precision_score(y_test, prediction), abs=TOLERANCE)
    assert result["recall"] == pytest.approx(recall_score(y_test, prediction), abs=TOLERANCE)
    assert result["f1_score"] == pytest.approx(f1_score(y_test, prediction), abs=TOLERANCE)
    assert result["confusion_matrix"] == confusion_matrix(y_test, prediction).tolist()
    assert result["roc_auc"] == pytest.approx(roc_auc_score(y_test, scores), abs=TOLERANCE)


@pytest.mark.parametrize("algorithm", BUILTIN_IDS)
def test_multiclass_metrics_match_weighted_sklearn_reference(algorithm):
    frame = iris_frame()
    result = run_all(frame, "species")[algorithm]
    y_test, prediction, _, _ = reference(frame, "species", algorithm)
    assert result["accuracy"] == pytest.approx(accuracy_score(y_test, prediction), abs=TOLERANCE)
    assert result["precision"] == pytest.approx(precision_score(y_test, prediction, average="weighted", zero_division=0), abs=TOLERANCE)
    assert result["recall"] == pytest.approx(recall_score(y_test, prediction, average="weighted", zero_division=0), abs=TOLERANCE)
    assert result["f1_score"] == pytest.approx(f1_score(y_test, prediction, average="weighted", zero_division=0), abs=TOLERANCE)
    assert result["confusion_matrix"] == confusion_matrix(y_test, prediction).tolist()
    assert result["classes"] == [0, 1, 2]
    assert result["roc_auc"] is None and result["roc_auc_applicable"] is False
    assert result["roc_auc_note"] == ROC_AUC_NOT_APPLICABLE


def test_imbalanced_three_class_data_uses_weighted_not_macro_average():
    from sklearn.datasets import make_classification
    x, y = make_classification(n_samples=600, n_features=8, n_informative=5, n_redundant=0,
                               n_classes=3, weights=[0.7, 0.2, 0.1], class_sep=0.6, random_state=5)
    frame = pd.DataFrame(x, columns=[f"f{i}" for i in range(8)])
    frame["label"] = y
    result = run_all(frame, "label")["decision_tree"]
    y_test, prediction, _, _ = reference(frame, "label", "decision_tree")
    weighted = f1_score(y_test, prediction, average="weighted", zero_division=0)
    macro = f1_score(y_test, prediction, average="macro", zero_division=0)
    assert abs(weighted - macro) > 1e-3
    assert result["f1_score"] == pytest.approx(weighted, abs=TOLERANCE)


def test_confusion_matrix_preserves_sorted_original_class_labels():
    frame = iris_frame()
    frame["species"] = frame["species"].map({0: "setosa", 1: "versicolor", 2: "virginica"})
    result = run_all(frame, "species")["random_forest"]
    matrix = np.asarray(result["confusion_matrix"])
    assert matrix.shape == (3, 3)
    assert result["classes"] == ["setosa", "versicolor", "virginica"]
    assert matrix.sum() == 30
