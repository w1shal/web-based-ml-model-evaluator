
"""Password hashing and JWT utilities for the ML Model Evaluator."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt


BCRYPT_MAX_PASSWORD_BYTES = 72
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with a newly generated salt."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password exceeds bcrypt's 72-byte limit")

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a stored bcrypt hash."""
    if not isinstance(password, str) or not isinstance(hashed, str):
        return False

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        return False

    try:
        return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError, OverflowError):
        return False


def _jwt_secret() -> str:
    """Load a signing secret from the environment, never from source code."""
    secret = os.environ.get("JWT_SECRET")

    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is required")

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 bytes long")

    return secret


def create_access_token(
    user_id: int,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Create a signed JWT containing identity and expiry claims."""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }

    return jwt.encode(
        payload,
        _jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Validate a JWT signature and expiry, then return its claims."""
    return jwt.decode(
        token,
        _jwt_secret(),
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "jti", "iat", "exp"]},
    )
