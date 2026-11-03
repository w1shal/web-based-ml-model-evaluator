import logging

import pytest

from app.config import validate_production_config
from app.models import User
from tests.conftest import GOOD


def test_http_redirected_to_https(client, monkeypatch):                         # TC-SEC-004
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    r = client.get("/auth/me", follow_redirects=False)
    assert r.status_code == 308 and r.headers["location"].startswith("https://")


def test_https_request_passes_and_sets_hsts(client, monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    r = client.get("/auth/me", headers={"X-Forwarded-Proto": "https"}, follow_redirects=False)
    assert r.status_code == 401                                                 # reached the app
    assert "max-age" in r.headers["strict-transport-security"]


def test_no_redirect_when_not_enforced_and_basic_headers(client):
    r = client.get("/auth/me", follow_redirects=False)
    assert r.status_code == 401
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "strict-transport-security" not in r.headers


def test_production_requires_strong_secret(monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        validate_production_config()
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError):
        validate_production_config()
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    validate_production_config()                                                # no error


def test_no_plaintext_password_in_db_or_logs(client, session_factory, caplog):  # TC-SEC-001
    with caplog.at_level(logging.DEBUG):
        client.post("/auth/register", json=GOOD)
        client.post("/auth/login", json={"identifier": "vivek", "password": GOOD["password"]})
    with session_factory() as db:
        stored = db.query(User).one().password_hash
    assert stored.startswith("$2") and GOOD["password"] not in stored
    assert GOOD["password"] not in caplog.text
