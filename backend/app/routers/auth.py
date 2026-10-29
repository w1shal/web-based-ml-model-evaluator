
"""Authentication routes: registration, login, logout and current user."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_auth, get_current_user
from ..models import RevokedToken, User
from ..schemas import LoginIn, RegisterIn
from ..security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])

# Used to perform password verification when the account is unknown.
# This helps reduce timing differences between login failure cases.
_DUMMY_HASH = hash_password("dummy-password-1")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterIn,
    db: Session = Depends(get_db),
):
    """Register a user with a securely hashed password."""

    normalized_email = str(body.email).lower()

    existing_user = db.scalar(
        select(User).where(
            or_(
                User.username == body.username,
                User.email == normalized_email,
            )
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=body.username,
        email=normalized_email,
        password_hash=hash_password(body.password),
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        ) from None

    return {
        "user_id": user.user_id,
        "message": "User registered",
    }


@router.post("/login")
def login(
    body: LoginIn,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return a JWT access token."""

    identifier = body.identifier.strip()

    user = db.scalar(
        select(User).where(
            or_(
                User.username == identifier,
                User.email == identifier.lower(),
            )
        )
    )

    stored_hash = user.password_hash if user else _DUMMY_HASH
    password_is_valid = verify_password(body.password, stored_hash)

    # Keep the status and public error identical for both failure cases.
    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(user.user_id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
        },
    }


@router.post("/logout")
def logout(
    auth: tuple[User, dict] = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """Revoke the current JWT until its original expiration time."""

    _, claims = auth

    jti = claims["jti"]
    expires_at = datetime.fromtimestamp(
        claims["exp"],
        tz=timezone.utc,
    ).replace(tzinfo=None)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        # Opportunistically remove expired revocation records.
        db.execute(
            delete(RevokedToken).where(
                RevokedToken.expires_at <= now
            )
        )

        # Store only the token ID and expiry, never the complete JWT.
        db.add(
            RevokedToken(
                jti=jti,
                expires_at=expires_at,
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Logged out"}


@router.get("/me")
def me(
    user: User = Depends(get_current_user),
):
    """Return the current authenticated user's non-sensitive profile."""

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
    }
