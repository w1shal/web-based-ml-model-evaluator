"""Password hashing and JWT utilities."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

ALGO = "HS256"
EXPIRE_MIN = 60
BCRYPT_MAX_PASSWORD_BYTES = 72


def _jwt_secret() -> str:
    """Load and validate the JWT signing secret from the environment."""
    secret = os.getenv("JWT_SECRET", "")

    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is required")

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 bytes long")

    return secret


def hash_password(pw: str) -> str:
    """Hash a password using bcrypt with a unique salt."""
    if not isinstance(pw, str):
        raise TypeError("Password must be a string")

    password_bytes = pw.encode("utf-8")

    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password exceeds bcrypt's 72-byte limit")

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    if not isinstance(pw, str) or not isinstance(hashed, str):
        return False

    password_bytes = pw.encode("utf-8")

    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        return False

    try:
        return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError, OverflowError):
        return False


def create_token(user_id: int, minutes: int = EXPIRE_MIN) -> str:
    """Create a signed JWT with identity and expiry claims."""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }

    return jwt.encode(payload, _jwt_secret(), algorithm=ALGO)


def decode_token(token: str) -> dict:
    """Validate a JWT signature and its required claims."""
    return jwt.decode(
        token,
        _jwt_secret(),
        algorithms=[ALGO],
        options={"require": ["sub", "jti", "iat", "exp"]},
    )


# Backward-compatible names used by the existing login/logout tests.


def create_access_token(
    user_id: int,
    expires_minutes: int = EXPIRE_MIN,
) -> str:
    return create_token(user_id, minutes=expires_minutes)


def decode_access_token(token: str) -> dict:
    return decode_token(token)