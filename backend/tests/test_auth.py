import pytest

from app.security import create_token, hash_password, verify_password
from tests.conftest import GOOD


def login(c, ident="vivek", pw="Strong123pw"):
    return c.post("/auth/login", json={"identifier": ident, "password": pw})


def test_register_ok(client):                                   # TC-001
    r = client.post("/auth/register", json=GOOD)
    assert r.status_code == 201 and "user_id" in r.json()


def test_hashing_salted_and_not_plaintext():                    # TC-002
    h1, h2 = hash_password("Strong123pw"), hash_password("Strong123pw")
    assert h1 != h2 and h1.startswith("$2") and "Strong123pw" not in h1
    assert verify_password("Strong123pw", h1)


def test_login_ok_and_token_accepted(client):                   # TC-003
    client.post("/auth/register", json=GOOD)
    r = login(client)
    assert r.status_code == 200
    tok = r.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 200


def test_login_with_email(client):
    client.post("/auth/register", json=GOOD)
    assert login(client, ident="VIVEK@example.com").status_code == 200


def test_logout_revokes_token(client):                          # TC-004
    client.post("/auth/register", json=GOOD)
    h = {"Authorization": f"Bearer {login(client).json()['access_token']}"}
    assert client.post("/auth/logout", headers=h).status_code == 200
    assert client.get("/auth/me", headers=h).status_code == 401


def test_logout_without_token(client):
    assert client.post("/auth/logout").status_code == 401


def test_invalid_credentials_identical(client):                 # TC-005
    client.post("/auth/register", json=GOOD)
    a, b = login(client, pw="wrongpass1"), login(client, ident="nobody")
    assert a.status_code == b.status_code == 401 and a.json() == b.json()
    assert a.json()["detail"] == "Invalid credentials"


def test_duplicate_registration(client):                        # TC-005a
    client.post("/auth/register", json=GOOD)
    assert client.post("/auth/register", json=GOOD).status_code == 409
    other_email = {**GOOD, "email": "other@example.com"}
    assert client.post("/auth/register", json=other_email).status_code == 409   # same username
    other_name = {**GOOD, "username": "someoneelse", "email": "VIVEK@EXAMPLE.COM"}
    assert client.post("/auth/register", json=other_name).status_code == 409    # same email, other case


@pytest.mark.parametrize("bad", [
    {**GOOD, "username": ""}, {**GOOD, "username": "bad name!"}, {**GOOD, "email": "nope"},
    {**GOOD, "password": "short1"}, {**GOOD, "password": "onlyletters"},
    {**GOOD, "password": "a1" * 40},
])
def test_invalid_fields(client, bad):                           # TC-005b
    r = client.post("/auth/register", json=bad)
    assert r.status_code == 400 and r.json()["error"]["fields"]


def test_missing_fields(client):
    r = client.post("/auth/register", json={})
    assert r.status_code == 400


def test_expired_and_tampered_token(client):                    # TC-005c
    client.post("/auth/register", json=GOOD)
    expired = create_token(1, minutes=-5)
    tampered = login(client).json()["access_token"][:-3] + "abc"
    for t in (expired, tampered):
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {t}"}).status_code == 401


def test_token_for_unknown_user_rejected(client):
    t = create_token(9999)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {t}"}).status_code == 401


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401
