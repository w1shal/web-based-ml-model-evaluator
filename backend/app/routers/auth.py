
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn
from ..security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])

# Used to perform a password verification even when the account is unknown.
# This helps reduce timing differences during login.
_DUMMY_HASH = hash_password("dummy-password-1")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterIn,
    db: Session = Depends(get_db),
):
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
        )

    return {
        "user_id": user.user_id,
        "message": "User registered",
    }


@router.post("/login")
def login(
    body: LoginIn,
    db: Session = Depends(get_db),
):
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

    # Same status and message for an unknown user or incorrect password.
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
