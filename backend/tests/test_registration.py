import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base, User
from app.security import verify_password


GOOD = {
    "username": "vivek",
    "email": "v@example.com",
    "password": "Strong123pw",
}


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
def client(test_db):
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_register_success(client):
    response = client.post("/auth/register", json=GOOD)

    assert response.status_code == 201
    assert response.json()["message"] == "User registered"
    assert "user_id" in response.json()
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_password_is_stored_as_bcrypt_hash(client, test_db):
    response = client.post("/auth/register", json=GOOD)

    assert response.status_code == 201

    with test_db() as db:
        user = db.scalar(
            select(User).where(User.username == GOOD["username"])
        )

        assert user is not None
        assert user.password_hash != GOOD["password"]
        assert verify_password(
            GOOD["password"], user.password_hash
        )


def test_duplicate_username_is_rejected(client):
    client.post("/auth/register", json=GOOD)

    second = {
        **GOOD,
        "email": "another@example.com",
    }

    response = client.post("/auth/register", json=second)

    assert response.status_code == 409


def test_duplicate_email_is_rejected_case_insensitively(client):
    client.post("/auth/register", json=GOOD)

    second = {
        **GOOD,
        "username": "another_user",
        "email": "V@EXAMPLE.COM",
    }

    response = client.post("/auth/register", json=second)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "bad",
    [
        {**GOOD, "username": ""},
        {**GOOD, "email": "not-an-email"},
        {**GOOD, "password": "short1"},
        {**GOOD, "password": "onlyletters"},
        {**GOOD, "password": "€" * 25},
    ],
)
def test_invalid_registration_fields_are_rejected(client, bad):
    response = client.post("/auth/register", json=bad)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert response.json()["error"]["fields"]