"""Shared test data helpers for evaluation-engine tests."""
import pandas as pd
import pytest
from sklearn.datasets import load_breast_cancer, load_iris, make_classification


@pytest.fixture
def dataset_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path))
    return tmp_path


def iris_df() -> pd.DataFrame:
    frame = load_iris(as_frame=True).frame
    frame.columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
    return frame


def cancer_df(n_features: int = 10) -> pd.DataFrame:
    data = load_breast_cancer(as_frame=True)
    cols = [column.replace(" ", "_") for column in data.feature_names[:n_features]]
    frame = data.data.iloc[:, :n_features].copy()
    frame.columns = cols
    frame["diagnosis"] = data.target
    return frame


def synthetic_df(rows: int, cols: int, classes: int = 2, seed: int = 0) -> pd.DataFrame:
    X, y = make_classification(n_samples=rows, n_features=cols, n_informative=max(2, cols // 3),
        n_redundant=0, n_classes=classes, n_clusters_per_class=1, random_state=seed)
    frame = pd.DataFrame(X, columns=[f"f{i}" for i in range(cols)])
    frame["label"] = y
    return frame


def features_of(df: pd.DataFrame, target: str) -> list[str]:
    return [column for column in df.columns if column != target]


def put_dataset(df: pd.DataFrame, name: str = "data.csv", owner_id=None) -> str:
    from app.services.dataset_store import store_dataset
    return store_dataset(df.to_csv(index=False).encode(), name, owner_id)


def eval_body(dataset_id: str, df: pd.DataFrame, target: str, algorithms, **extra) -> dict:
    return {"dataset_id": dataset_id, "target_column": target,
        "feature_columns": features_of(df, target), "algorithms": list(algorithms), **extra}
