
"""Shared authentication dependencies for protected and guest-capable routes."""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import RevokedToken, User
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _resolve(
    creds: HTTPAuthorizationCredentials,
    db: Session,
) -> User:
    """Resolve a valid, unexpired, non-revoked token to an existing user."""
    try:
        payload = decode_access_token(creds.credentials)
        subject = payload["sub"]
        token_id = payload["jti"]

        if not isinstance(subject, str) or not subject.isdecimal():
            raise ValueError("Invalid token subject")

        user_id = int(subject)

        if user_id <= 0:
            raise ValueError("Invalid token subject")

        if (
            not isinstance(token_id, str)
            or not token_id
            or len(token_id) > 64
        ):
            raise ValueError("Invalid token identifier")

    except (
        jwt.PyJWTError,
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
    ):
        raise _unauthorized("Invalid or expired token") from None

    if db.get(RevokedToken, token_id) is not None:
        raise _unauthorized("Token has been revoked")

    user = db.get(User, user_id)

    if user is None:
        raise _unauthorized("Invalid or expired token")

    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _unauthorized("Not authenticated")

    return _resolve(creds, db)


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Allow guests, but reject supplied invalid or revoked credentials."""
    return _resolve(creds, db) if creds is not None else None
