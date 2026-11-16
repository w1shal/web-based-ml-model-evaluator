"""Unit tests for configuration, password hashing, JWT helpers and input schemas."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app import config, db, security
from app.schemas import LoginIn, RegisterIn

# ---------------------------------------------------------------- config.py


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1", True), ("true", True), (" YES ", True), ("on", True),
     ("0", False), ("false", False), ("off", False), ("", False), ("maybe", False)],
)
def test_env_bool_parses_truthy_and_falsy_values(monkeypatch, raw, expected):
    monkeypatch.setenv("SOME_FLAG", raw)
    assert config.env_bool("SOME_FLAG") is expected


def test_env_bool_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_FLAG", raising=False)
    assert config.env_bool("SOME_FLAG") is False
    assert config.env_bool("SOME_FLAG", default=True) is True


def test_cors_origins_default_and_custom(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert config.cors_origins() == ["http://localhost:3000", "http://localhost:5173"]

    monkeypatch.setenv("CORS_ORIGINS", " https://a.example , ,https://b.example ")
    assert config.cors_origins() == ["https://a.example", "https://b.example"]


def test_validate_production_config_is_noop_without_https(monkeypatch):
    monkeypatch.delenv("ENFORCE_HTTPS", raising=False)
    monkeypatch.setenv("JWT_SECRET", "")
    config.validate_production_config()  # must not raise


@pytest.mark.parametrize("secret", ["", "change-me", "dev-only-change-me", "short-secret"])
def test_validate_production_config_rejects_weak_secrets(monkeypatch, secret):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.setenv("JWT_SECRET", secret)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        config.validate_production_config()


def test_validate_production_config_accepts_strong_secret(monkeypatch):
    monkeypatch.setenv("ENFORCE_HTTPS", "1")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    config.validate_production_config()


# -------------------------------------------------------------- security.py


def test_jwt_secret_missing_raises(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="required"):
        security.create_token(1)


def test_jwt_secret_too_short_raises(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(RuntimeError, match="32 bytes"):
        security.create_token(1)


def test_hash_and_verify_password_roundtrip():
    hashed = security.hash_password("Strong123pw")
    assert hashed != "Strong123pw"
    assert hashed.startswith("$2")
    assert security.verify_password("Strong123pw", hashed) is True
    assert security.verify_password("Wrong123pw", hashed) is False


def test_hash_password_uses_unique_salts():
    assert security.hash_password("Strong123pw") != security.hash_password("Strong123pw")


def test_hash_password_rejects_non_string_and_oversized_input():
    with pytest.raises(TypeError):
        security.hash_password(12345)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="72-byte"):
        security.hash_password("a1" * 40)


@pytest.mark.parametrize(
    ("password", "hashed"),
    [(None, "$2b$12$abc"), ("pw", None), ("a1" * 40, "$2b$12$abc"), ("Strong123pw", "not-a-bcrypt-hash")],
)
def test_verify_password_returns_false_for_bad_inputs(password, hashed):
    assert security.verify_password(password, hashed) is False


def test_token_roundtrip_contains_required_claims():
    token = security.create_access_token(7, expires_minutes=5)
    claims = security.decode_access_token(token)
    assert claims["sub"] == "7"
    assert isinstance(claims["jti"], str) and len(claims["jti"]) == 32
    assert claims["exp"] - claims["iat"] == 300


def test_tokens_have_unique_jti():
    first = security.decode_token(security.create_token(1))
    second = security.decode_token(security.create_token(1))
    assert first["jti"] != second["jti"]


def test_expired_token_is_rejected():
    token = security.create_token(1, minutes=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token)


def test_token_signed_with_other_secret_is_rejected():
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"sub": "1", "jti": "abc", "iat": now, "exp": now + timedelta(minutes=5)},
        "an-attacker-controlled-secret-of-32-bytes!",
        algorithm="HS256",
    )
    with pytest.raises(jwt.InvalidSignatureError):
        security.decode_token(forged)


def test_token_missing_required_claim_is_rejected():
    now = datetime.now(timezone.utc)
    import os

    token = jwt.encode({"sub": "1", "iat": now, "exp": now + timedelta(minutes=5)},
                       os.environ["JWT_SECRET"], algorithm="HS256")
    with pytest.raises(jwt.MissingRequiredClaimError):
        security.decode_token(token)


# --------------------------------------------------------------- schemas.py


def test_register_schema_accepts_valid_input():
    body = RegisterIn(username="user.name-1", email="u@example.com", password="Strong123pw")
    assert body.username == "user.name-1"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("username", "ab"),
        ("username", "bad name"),
        ("username", "x" * 51),
        ("email", "not-an-email"),
        ("password", "short1"),
        ("password", "onlyletters"),
        ("password", "1234567890"),
        ("password", "é1" * 30),  # 60 characters but 90 bytes in UTF-8
    ],
)
def test_register_schema_rejects_invalid_fields(field, value):
    data = {"username": "valid_user", "email": "u@example.com", "password": "Strong123pw"}
    data[field] = value
    with pytest.raises(ValidationError):
        RegisterIn(**data)


def test_login_schema_requires_non_empty_values():
    with pytest.raises(ValidationError):
        LoginIn(identifier="", password="x")
    with pytest.raises(ValidationError):
        LoginIn(identifier="x", password="")


# -------------------------------------------------------------------- db.py


def test_get_db_yields_session_and_closes_it(monkeypatch):
    events = []

    class FakeSession:
        def close(self):
            events.append("closed")

    monkeypatch.setattr(db, "SessionLocal", FakeSession)
    generator = db.get_db()
    session = next(generator)
    assert isinstance(session, FakeSession)
    assert events == []
    with pytest.raises(StopIteration):
        next(generator)
    assert events == ["closed"]


def test_legacy_database_module_reexports_single_engine():
    from app import database

    assert database.engine is db.engine
    assert database.Base is db.Base
    assert database.get_db is db.get_db
