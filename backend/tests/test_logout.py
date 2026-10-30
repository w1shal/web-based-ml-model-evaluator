
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base, RevokedToken
from app.security import create_access_token, decode_access_token


GOOD = {
    "username": "vivek_logout_test",
    "email": "vivek.logout@example.com",
    "password": "Strong123pw",
}

TEST_SECRET = "logout-testing-secret-key-at-least-32-bytes"


@pytest.fixture
def test_db():
    """Use an isolated in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    yield testing_session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(test_db, monkeypatch):
    """Configure a test-only JWT secret and isolated database."""
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)

    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def create_logged_in_user(client):
    """Register and log in a test user; return its JWT and headers."""
    registered = client.post("/auth/register", json=GOOD)
    assert registered.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "identifier": GOOD["username"],
            "password": GOOD["password"],
        },
    )
    assert response.status_code == 200

    token = response.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def test_logout_revokes_token(client):
    """The same token must work before logout and fail afterward."""
    token, headers = create_logged_in_user(client)

    before = client.get("/auth/me", headers=headers)
    assert before.status_code == 200
    assert before.json()["username"] == GOOD["username"]

    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logged out"}

    after = client.get("/auth/me", headers=headers)
    assert after.status_code == 401


def test_logout_records_jti_not_raw_token(client, test_db):
    """The revocation table records the JWT ID, not the complete JWT."""
    token, headers = create_logged_in_user(client)

    claims = decode_access_token(token)

    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 200

    with test_db() as db:
        record = db.get(RevokedToken, claims["jti"])

        assert record is not None
        assert record.expires_at is not None
        assert token != record.jti


def test_logout_without_token_returns_401(client):
    response = client.post("/auth/logout")
    assert response.status_code == 401


def test_protected_endpoint_rejects_malformed_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_protected_endpoint_rejects_expired_token(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)

    expired_token = create_access_token(
        user_id=1,
        expires_minutes=-5,
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_logout_removes_expired_revocation_records(client, test_db):
    """Logout cleans expired entries without retaining them indefinitely."""
    _, headers = create_logged_in_user(client)

    old_record = RevokedToken(
        jti="old-expired-test-token",
        expires_at=(
            datetime.now(timezone.utc) - timedelta(days=1)
        ).replace(tzinfo=None),
    )

    with test_db() as db:
        db.add(old_record)
        db.commit()

    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 200

    with test_db() as db:
        assert db.get(RevokedToken, "old-expired-test-token") is None
