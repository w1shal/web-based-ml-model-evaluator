import logging

import pytest

from app.config import validate_production_config
from app.models import User
from tests.conftest import GOOD


def test_http_is_redirected_to_https(client, monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.delenv("TRUST_PROXY", raising=False)

    response = client.get("/auth/me", follow_redirects=False)

    assert response.status_code == 308
    assert response.headers["location"].startswith("https://")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_trusted_https_proxy_request_passes_and_sets_hsts(client, monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.setenv("TRUST_PROXY", "1")

    response = client.get(
        "/auth/me",
        headers={"X-Forwarded-Proto": "https"},
        follow_redirects=False,
    )

    assert response.status_code == 401  # Request reached auth, not HTTPS redirect.
    assert "max-age=31536000" in response.headers["strict-transport-security"]


def test_untrusted_forwarded_proto_cannot_bypass_https(client, monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.delenv("TRUST_PROXY", raising=False)

    response = client.get(
        "/auth/me",
        headers={"X-Forwarded-Proto": "https"},
        follow_redirects=False,
    )

    assert response.status_code == 308
    assert response.headers["location"].startswith("https://")


def test_http_local_development_still_works(client, monkeypatch):
    monkeypatch.delenv("ENFORCE_HTTPS", raising=False)
    monkeypatch.delenv("TRUST_PROXY", raising=False)

    response = client.get("/auth/me", follow_redirects=False)

    assert response.status_code == 401
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "strict-origin-when-cross-origin" == response.headers["referrer-policy"]
    assert "strict-transport-security" not in response.headers


def test_production_requires_a_strong_jwt_secret(monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config()

    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config()

    monkeypatch.setenv("JWT_SECRET", "dev-only-change-me")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config()

    monkeypatch.setenv("JWT_SECRET", "x" * 48)
    validate_production_config()


def test_no_plaintext_password_in_db_or_logs(client, session_factory, caplog):
    with caplog.at_level(logging.DEBUG):
        client.post("/auth/register", json=GOOD)
        client.post(
            "/auth/login",
            json={"identifier": "vivek", "password": GOOD["password"]},
        )

    with session_factory() as db:
        stored_hash = db.query(User).one().password_hash

    assert stored_hash.startswith("$2")
    assert GOOD["password"] not in stored_hash
    assert GOOD["password"] not in caplog.text
