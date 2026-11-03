
import jwt
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base
from app.security import create_access_token, decode_access_token


GOOD = {
    "username": "vivek",
    "email": "v@example.com",
    "password": "Strong123pw",
}

TEST_SECRET = "local-testing-secret-key-at-least-32-bytes"


@pytest.fixture
def test_db():
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


def register_user(client):
    response = client.post("/auth/register", json=GOOD)
    assert response.status_code == 201


def test_login_success_returns_jwt(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "identifier": "vivek",
            "password": "Strong123pw",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["user"]["username"] == "vivek"
    assert "password" not in data
    assert "password_hash" not in data

    claims = decode_access_token(data["access_token"])
    assert claims["sub"] == str(data["user"]["user_id"])
    assert claims["jti"]
    assert claims["exp"] > claims["iat"]


def test_login_accepts_email_identifier(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "identifier": "V@EXAMPLE.COM",
            "password": "Strong123pw",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_wrong_password_and_unknown_user_have_same_error(client):
    register_user(client)

    wrong_password = client.post(
        "/auth/login",
        json={
            "identifier": "vivek",
            "password": "Wrong123pw",
        },
    )

    unknown_user = client.post(
        "/auth/login",
        json={
            "identifier": "unknown-user",
            "password": "Wrong123pw",
        },
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()
    assert wrong_password.json()["detail"] == "Invalid credentials"


def test_expired_token_is_rejected(client):
    expired_token = create_access_token(1, expires_minutes=-1)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_tampered_token_is_rejected(client):
    token = create_access_token(1)
    header, payload, signature = token.split(".")

    replacement = "A" if signature[0] != "A" else "B"
    tampered_token = f"{header}.{payload}.{replacement}{signature[1:]}"

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)
