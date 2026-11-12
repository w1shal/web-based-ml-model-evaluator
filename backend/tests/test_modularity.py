import ast
from pathlib import Path

from sklearn.dummy import DummyClassifier

from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm
from tests.ml_helpers import eval_body, iris_df, put_dataset


def test_new_algorithm_is_discoverable_and_usable_without_api_changes(client, dataset_dir):
    register_algorithm(AlgorithmSpec(id="stub_majority", name="Majority Stub",
                                     factory=lambda seed, rows: DummyClassifier(strategy="most_frequent")))
    try:
        ids = [item["id"] for item in client.get("/algorithms").json()["items"]]
        assert "stub_majority" in ids
        frame = iris_df()
        response = client.post("/evaluations", json=eval_body(put_dataset(frame), frame, "species", ["stub_majority"]))
        assert response.status_code == 200 and response.json()["results"][0]["algorithm"] == "stub_majority"
    finally:
        unregister_algorithm("stub_majority")


def test_ml_engine_has_no_web_or_database_imports():
    forbidden = ("fastapi", "starlette", "sqlalchemy", "app.routers", "app.models", "app.db", "app.services", "app.deps")
    offenders = []
    folder = Path(__file__).resolve().parent.parent / "app" / "ml"
    for path in folder.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [item.name for item in node.names] if isinstance(node, ast.Import) else []
            if isinstance(node, ast.ImportFrom):
                names = [("." * node.level) + (node.module or "")]
            offenders.extend(f"{path.name}: {name}" for name in names if name.lstrip(".").startswith(forbidden))
    assert offenders == []
