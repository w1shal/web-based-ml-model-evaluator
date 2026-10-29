
"""Shared authentication dependencies for protected API routes."""

import jwt
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import RevokedToken, User
from .security import decode_access_token


bearer = HTTPBearer(auto_error=False)


def _resolve_token(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
) -> tuple[User, dict]:
    """Validate a JWT, reject revoked tokens, and resolve its user."""

    try:
        claims = decode_access_token(credentials.credentials)

        user_id = int(claims["sub"])
        jti = claims["jti"]

        if not isinstance(jti, str) or not jti:
            raise ValueError("Invalid token identifier")

    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    # A validly signed JWT must still be rejected if it was revoked.
    if db.get(RevokedToken, jti) is not None:
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user, claims


def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> tuple[User, dict]:
    """Require authentication and return the user plus verified JWT claims."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _resolve_token(credentials, db)


def get_current_user(
    auth: tuple[User, dict] = Depends(get_current_auth),
) -> User:
    """Return the authenticated user for protected endpoints."""
    return auth[0]


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Allow guests, but reject any supplied invalid or revoked token."""

    if authorization is None:
        return None

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, _ = _resolve_token(credentials, db)
    return user
