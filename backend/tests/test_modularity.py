"""Architecture checks for the pluggable ML engine."""
import ast
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier

from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm
from app.services.dataset_store import store_dataset


def test_new_algorithm_is_discoverable_and_usable_without_api_changes(client, tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path / "datasets"))
    algorithm_id = "stub_majority"
    register_algorithm(AlgorithmSpec(
        id=algorithm_id,
        name="Majority Stub",
        factory=lambda seed, rows: DummyClassifier(strategy="most_frequent"),
    ))
    try:
        ids = [item["id"] for item in client.get("/algorithms").json()["items"]]
        assert algorithm_id in ids
        frame = pd.DataFrame({
            "feature": list(range(60)),
            "target": ["yes" if index % 2 else "no" for index in range(60)],
        })
        dataset_id = store_dataset(frame.to_csv(index=False).encode("utf-8"), "stub.csv", None)
        response = client.post("/evaluations", json={
            "dataset_id": dataset_id,
            "target_column": "target",
            "feature_columns": ["feature"],
            "algorithms": [algorithm_id],
            "test_size": 0.2,
            "missing_value_strategy": "median_imputation",
        })
        assert response.status_code == 200, response.text
        assert response.json()["results"][0]["algorithm"] == algorithm_id
    finally:
        unregister_algorithm(algorithm_id)


def test_ml_engine_has_no_web_or_database_imports():
    forbidden = (
        "fastapi", "starlette", "sqlalchemy", "app.routers", "app.models",
        "app.db", "app.services", "app.deps",
    )
    offenders = []
    folder = Path(__file__).resolve().parent.parent / "app" / "ml"
    for path in folder.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [("." * node.level) + (node.module or "")]
            else:
                continue
            offenders.extend(f"{path.name}: {name}" for name in names
                             if any(name.lstrip(".").startswith(item) for item in forbidden))
    assert offenders == []
