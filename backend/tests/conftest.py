import os

# Use a sufficiently long, test-only JWT key before importing app modules.
os.environ["JWT_SECRET"] = "sprint2-test-only-jwt-secret-at-least-32-bytes"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base
from app.ratelimit import limiter  # FIX: required by _clean_state
from app.services.history import save_run

GOOD = {
    "username": "vivek",
    "email": "vivek@example.com",
    "password": "Strong123pw",
}

SAMPLE_RESULTS = [
    {
        "algorithm": "random_forest",
        "accuracy": 0.92,
        "precision": 0.91,
        "recall": 0.90,
        "f1_score": 0.905,
        "roc_auc": 0.95,
        "confusion_matrix": [[45, 5], [4, 46]],
    },
    {
        "algorithm": "logistic_regression",
        "accuracy": 0.88,
        "precision": 0.87,
        "recall": 0.86,
        "f1_score": 0.865,
        "roc_auc": 0.93,
        "confusion_matrix": [[43, 7], [5, 45]],
    },
]


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """Generous limits for ordinary tests; rate-limit tests override them."""
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "1000")
    monkeypatch.setenv("RATE_LIMIT_REGISTER_MAX", "1000")
    monkeypatch.delenv("ENFORCE_HTTPS", raising=False)
    monkeypatch.delenv("TRUST_PROXY", raising=False)

    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield Session
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(session_factory):
    return TestClient(app)


@pytest.fixture
def make_user(client):
    """Register + log in a user; returns {'user_id', 'headers'}."""

    def _make(username="vivek", password="Strong123pw"):
        r = client.post(
            "/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
            },
        )
        assert r.status_code == 201, r.text

        tok = client.post(
            "/auth/login",
            json={"identifier": username, "password": password},
        ).json()["access_token"]

        return {
            "user_id": r.json()["user_id"],
            "headers": {"Authorization": f"Bearer {tok}"},
        }

    return _make


@pytest.fixture
def make_run(session_factory):
    """Insert an evaluation run directly (stands in for POST /evaluations)."""

    def _make(user_id, dataset="iris.csv", results=None, timestamp=None):
        with session_factory() as db:
            run = save_run(
                db,
                user_id,
                dataset_name=dataset,
                target_column="species",
                feature_columns=["sepal_length", "sepal_width"],
                split_ratio=0.2,
                results=results or SAMPLE_RESULTS,
                timestamp=timestamp,
            )
            return run.run_id

    return _make