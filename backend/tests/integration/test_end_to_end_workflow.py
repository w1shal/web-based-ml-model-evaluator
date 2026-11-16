"""End-to-end integration tests: the full HTTP stack (routers, auth, ML engine,
dataset store, persistence and reporting) exercised together through the API."""

import csv
import io
import os
from datetime import datetime, timedelta, timezone

import jwt
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sklearn.datasets import load_breast_cancer, load_iris
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.ml.gate import GateTimeout
from app.services import evaluation_service
from app.services.dataset_store import store_dataset

pytestmark = pytest.mark.integration


@pytest.fixture
def dataset_dir(tmp_path, monkeypatch):
    directory = tmp_path / "datasets"
    monkeypatch.setenv("DATASET_DIR", str(directory))
    return directory


def _frame(loader, target):
    source = loader(as_frame=True)
    frame = source.data.copy()
    frame[target] = source.target
    return frame


def _upload(frame, name, owner_id=None):
    return store_dataset(frame.to_csv(index=False).encode("utf-8"), name, owner_id)


def _body(dataset_id, frame, target, algorithms, **extra):
    return {
        "dataset_id": dataset_id,
        "target_column": target,
        "feature_columns": [c for c in frame.columns if c != target],
        "algorithms": algorithms,
        **extra,
    }


# ------------------------------------------------------------- full journeys


def test_registered_user_full_journey(client, dataset_dir):
    """register -> login -> me -> evaluate -> fetch -> history -> reports -> delete -> logout."""
    credentials = {"username": "e2e_user", "email": "E2E@Example.com", "password": "Strong123pw"}
    assert client.post("/auth/register", json=credentials).status_code == 201

    login = client.post("/auth/login", json={"identifier": "e2e@example.com", "password": "Strong123pw"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/auth/me", headers=headers).json()
    assert me["username"] == "e2e_user" and me["email"] == "e2e@example.com"

    algorithms = client.get("/algorithms").json()["items"]
    assert {item["id"] for item in algorithms} >= {"logistic_regression", "decision_tree", "random_forest", "svm", "knn"}

    frame = _frame(load_breast_cancer, "diagnosis")
    dataset_id = _upload(frame, "cancer.csv", owner_id=me["user_id"])
    evaluation = client.post(
        "/evaluations",
        json=_body(dataset_id, frame, "diagnosis", ["logistic_regression", "random_forest", "knn"], test_size=0.25),
        headers=headers,
    )
    assert evaluation.status_code == 200, evaluation.text
    result = evaluation.json()
    run_id = result["run_id"]
    assert result["status"] == "completed"
    assert result["dataset"] == {"name": "cancer.csv", "rows": 569, "train_rows": 426, "test_rows": 143}
    assert len(result["comparison"]["ranking"]) == 3
    assert result["comparison"]["ranking"][0]["rank"] == 1
    for row in result["results"]:
        assert row["roc_auc_applicable"] is True and 0.5 < row["roc_auc"] <= 1.0
        assert sum(map(sum, row["confusion_matrix"])) == 143

    # The persisted run must reproduce exactly what the POST returned.
    fetched = client.get(f"/evaluations/{run_id}", headers=headers).json()
    assert fetched["dataset"] == result["dataset"]
    assert fetched["comparison"] == result["comparison"]
    for posted, stored in zip(result["results"], fetched["results"], strict=True):
        for key in ("algorithm", "accuracy", "precision", "recall", "f1_score", "roc_auc", "confusion_matrix"):
            assert stored[key] == pytest.approx(posted[key]) if isinstance(posted[key], float) else stored[key] == posted[key]

    history = client.get("/history", headers=headers).json()
    assert history["total"] == 1 and history["items"][0]["run_id"] == run_id
    detail = client.get(f"/history/{run_id}", headers=headers).json()
    assert detail["split_ratio"] == 0.25
    assert detail["algorithms"] == ["logistic_regression", "random_forest", "knn"]
    assert detail["confusion_matrix_labels"]["knn"] == [0, 1]

    csv_response = client.get(f"/reports/{run_id}/csv", headers=headers)
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(csv_response.text)))
    assert [row["algorithm"] for row in rows] == ["logistic_regression", "random_forest", "knn"]
    assert float(rows[0]["accuracy"]) == pytest.approx(result["results"][0]["accuracy"])

    pdf_response = client.get(f"/reports/{run_id}/pdf", headers=headers)
    assert pdf_response.status_code == 200 and pdf_response.content.startswith(b"%PDF")
    pdf_text = "".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf_response.content)).pages)
    assert "cancer.csv" in pdf_text and run_id in pdf_text

    assert client.delete(f"/history/{run_id}", headers=headers).status_code == 200
    assert client.get(f"/history/{run_id}", headers=headers).status_code == 404
    assert client.get(f"/evaluations/{run_id}", headers=headers).status_code == 404
    assert client.get(f"/reports/{run_id}/csv", headers=headers).status_code == 404

    assert client.post("/auth/logout", headers=headers).status_code == 200
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.get("/history", headers=headers).status_code == 401


def test_guest_journey_is_not_saved_to_any_history(client, make_user, dataset_dir):
    frame = _frame(load_iris, "species")
    dataset_id = _upload(frame, "iris.csv")
    response = client.post("/evaluations", json=_body(dataset_id, frame, "species", ["decision_tree", "svm"]))
    assert response.status_code == 200, response.text
    run_id = response.json()["run_id"]
    assert all(row["roc_auc"] is None for row in response.json()["results"])  # multiclass

    # Guest runs are retrievable and exportable without an account...
    assert client.get(f"/evaluations/{run_id}").status_code == 200
    assert client.get(f"/reports/{run_id}/csv").status_code == 200
    assert client.get(f"/reports/{run_id}/pdf").status_code == 200

    # ...but never appear in a registered user's history.
    user = make_user("observer")
    assert client.get("/history", headers=user["headers"]).json()["total"] == 0
    assert client.get(f"/history/{run_id}", headers=user["headers"]).status_code == 403


def test_runs_are_isolated_between_users(client, make_user, dataset_dir):
    alice, bob = make_user("alice"), make_user("bob")
    frame = _frame(load_iris, "species")
    dataset_id = _upload(frame, "iris.csv", owner_id=alice["user_id"])
    run_id = client.post("/evaluations", json=_body(dataset_id, frame, "species", ["knn"]),
                         headers=alice["headers"]).json()["run_id"]

    assert client.get(f"/evaluations/{run_id}").status_code == 401
    assert client.get(f"/evaluations/{run_id}", headers=bob["headers"]).status_code == 403
    assert client.get(f"/history/{run_id}", headers=bob["headers"]).status_code == 403
    assert client.delete(f"/history/{run_id}", headers=bob["headers"]).status_code == 403
    assert client.get(f"/reports/{run_id}/pdf", headers=bob["headers"]).status_code == 404
    assert client.get("/history", headers=bob["headers"]).json()["total"] == 0
    assert client.get("/history", headers=alice["headers"]).json()["total"] == 1


def test_mixed_type_dataset_with_missing_values(client, dataset_dir):
    frame = pd.DataFrame({
        "age": [25, 32, None, 45, 51, 23, 38, 41, 29, 60] * 4,
        "plan": ["basic", "pro", "pro", None, "basic", "team", "pro", "basic", "team", "pro"] * 4,
        "churn": [0, 1, 0, 1, 1, 0, 1, 0, 0, 1] * 4,
    })
    dataset_id = _upload(frame, "churn.csv")

    imputed = client.post("/evaluations", json=_body(dataset_id, frame, "churn", ["logistic_regression"])).json()
    assert imputed["preprocessing"]["numeric_features"] == ["age"]
    assert imputed["preprocessing"]["categorical_features"] == ["plan"]
    assert imputed["dataset"]["rows"] == 40

    dropped = client.post("/evaluations", json=_body(
        dataset_id, frame, "churn", ["logistic_regression"], missing_value_strategy="drop_rows")).json()
    assert dropped["preprocessing"]["rows_dropped_missing_features"] == 8
    assert dropped["dataset"]["rows"] == 32


def test_partial_failure_is_persisted_and_blocks_reports(client, dataset_dir, monkeypatch):
    from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm

    class Broken:
        def fit(self, X, y):
            raise RuntimeError("cannot train")

    register_algorithm(AlgorithmSpec("broken_integration", "Broken", lambda seed, rows: Broken()))
    try:
        frame = _frame(load_iris, "species")
        dataset_id = _upload(frame, "iris.csv")
        response = client.post("/evaluations", json=_body(dataset_id, frame, "species", ["knn", "broken_integration"]))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "partial"
        assert [row["algorithm"] for row in body["comparison"]["ranking"]] == ["knn"]

        fetched = client.get(f"/evaluations/{body['run_id']}").json()
        assert fetched["status"] == "partial"
        assert fetched["results"][1] == {
            "algorithm": "broken_integration", "name": "Broken", "status": "failed",
            "error": "Training failed (RuntimeError)", "duration_ms": fetched["results"][1]["duration_ms"],
        }
        assert client.get(f"/reports/{body['run_id']}/csv").status_code == 409
    finally:
        unregister_algorithm("broken_integration")


def test_server_busy_returns_503_with_retry_after(client, dataset_dir, monkeypatch):
    class BusyGate:
        def slot(self):
            raise GateTimeout()

    monkeypatch.setattr(evaluation_service, "evaluation_gate", BusyGate())
    frame = _frame(load_iris, "species")
    dataset_id = _upload(frame, "iris.csv")
    response = client.post("/evaluations", json=_body(dataset_id, frame, "species", ["knn"]))
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"


# -------------------------------------------------------- auth edge cases


def test_optional_auth_rejects_non_bearer_authorization(client, dataset_dir):
    frame = _frame(load_iris, "species")
    dataset_id = _upload(frame, "iris.csv")
    response = client.post("/evaluations", json=_body(dataset_id, frame, "species", ["knn"]),
                           headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authorization header"


def test_token_with_non_string_jti_is_rejected(client, make_user):
    user = make_user("jti_user")
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": str(user["user_id"]), "jti": 123, "iat": now, "exp": now + timedelta(minutes=5)},
                       os.environ["JWT_SECRET"], algorithm="HS256")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_for_deleted_user_is_rejected(client, make_user, session_factory):
    from app.models import User

    user = make_user("ghost")
    with session_factory() as db:
        db.delete(db.get(User, user["user_id"]))
        db.commit()
    assert client.get("/auth/me", headers=user["headers"]).status_code == 401


def test_validation_errors_use_uniform_envelope(client):
    response = client.post("/auth/register", json={"username": "x", "email": "bad"})
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "INVALID_REQUEST"
    assert {field["field"] for field in error["fields"]} >= {"username", "email", "password"}


def test_security_headers_present_on_every_response(client):
    for response in (client.get("/algorithms"), client.get("/history"), client.get("/does-not-exist")):
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"


def test_cors_preflight_allows_configured_dev_origin(client):
    response = client.options("/auth/login", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


# -------------------------------------------------------------- lifespan


@pytest.fixture
def isolated_engine(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    monkeypatch.setattr(main_module, "engine", engine)
    yield engine
    engine.dispose()


def test_lifespan_creates_tables(isolated_engine, monkeypatch):
    from sqlalchemy import inspect

    monkeypatch.delenv("ENFORCE_HTTPS", raising=False)
    with TestClient(main_module.app):
        tables = set(inspect(isolated_engine).get_table_names())
    assert {"users", "evaluation_runs", "algorithm_results", "revoked_tokens"} <= tables


def test_lifespan_refuses_https_deployment_with_weak_secret(isolated_engine, monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.setenv("JWT_SECRET", "change-me")
    with pytest.raises(RuntimeError, match="JWT_SECRET"), TestClient(main_module.app):
        pass  # pragma: no cover
