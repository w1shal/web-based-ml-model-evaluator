import pytest

from app.security import create_token, hash_password, verify_password
from tests.conftest import GOOD


def login(client, identifier="vivek", password="Strong123pw"):
    return client.post(
        "/auth/login",
        json={"identifier": identifier, "password": password},
    )


def test_register_ok(client):  # TC-001
    response = client.post("/auth/register", json=GOOD)
    assert response.status_code == 201
    assert "user_id" in response.json()


def test_hashing_is_salted_and_not_plaintext():  # TC-002
    first = hash_password("Strong123pw")
    second = hash_password("Strong123pw")
    assert first != second
    assert first.startswith("$2")
    assert "Strong123pw" not in first
    assert verify_password("Strong123pw", first)


def test_login_ok_and_token_is_accepted(client):  # TC-003
    assert client.post("/auth/register", json=GOOD).status_code == 201
    response = login(client)
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).status_code == 200


def test_login_accepts_email_identifier(client):
    assert client.post("/auth/register", json=GOOD).status_code == 201
    assert login(client, identifier="VIVEK@example.com").status_code == 200


def test_logout_revokes_token(client):  # TC-004
    assert client.post("/auth/register", json=GOOD).status_code == 201
    token = login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.post("/auth/logout", headers=headers).status_code == 200
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_logout_without_token_is_unauthorized(client):
    assert client.post("/auth/logout").status_code == 401


def test_invalid_credentials_have_identical_responses(client):  # TC-005
    assert client.post("/auth/register", json=GOOD).status_code == 201
    wrong_password = login(client, password="wrongpass1")
    unknown_user = login(client, identifier="nobody")

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()
    assert wrong_password.json()["detail"] == "Invalid credentials"


def test_duplicate_registration_is_rejected(client):  # TC-005a
    assert client.post("/auth/register", json=GOOD).status_code == 201
    assert client.post("/auth/register", json=GOOD).status_code == 409

    duplicate_username = {**GOOD, "email": "other@example.com"}
    assert client.post("/auth/register", json=duplicate_username).status_code == 409

    duplicate_email = {
        **GOOD,
        "username": "someoneelse",
        "email": "VIVEK@EXAMPLE.COM",
    }
    assert client.post("/auth/register", json=duplicate_email).status_code == 409


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {**GOOD, "username": ""},
        {**GOOD, "username": "bad name!"},
        {**GOOD, "email": "not-an-email"},
        {**GOOD, "password": "short1"},
        {**GOOD, "password": "onlyletters"},
        {**GOOD, "password": "a1" * 40},
    ],
)
def test_invalid_registration_fields_are_rejected(client, invalid_payload):  # TC-005b
    response = client.post("/auth/register", json=invalid_payload)
    assert response.status_code == 400
    assert response.json()["error"]["fields"]


def test_missing_registration_fields_are_rejected(client):
    response = client.post("/auth/register", json={})
    assert response.status_code == 400


def test_expired_and_tampered_tokens_are_rejected(client):  # TC-005c
    assert client.post("/auth/register", json=GOOD).status_code == 201
    expired_token = create_token(1, minutes=-5)
    valid_token = login(client).json()["access_token"]
    tampered_token = valid_token[:-3] + "abc"

    for token in (expired_token, tampered_token):
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


def test_token_for_unknown_user_is_rejected(client):
    token = create_token(9999)
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    assert client.get("/auth/me").status_code == 401
