
"""Password hashing utilities for the ML Model Evaluator."""

import bcrypt


BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with a newly generated salt."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    password_bytes = password.encode("utf-8")

    # bcrypt processes at most 72 bytes. Reject longer inputs rather
    # than silently truncating them or hashing a different password.
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password exceeds bcrypt's 72-byte limit")

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return password_hash.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a previously stored bcrypt hash."""
    if not isinstance(password, str) or not isinstance(hashed, str):
        return False

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        return False

    try:
        return bcrypt.checkpw(
            password_bytes,
            hashed.encode("utf-8"),
        )
    except (ValueError, TypeError, OverflowError):
        # Invalid stored hashes must not crash authentication.
        return False
