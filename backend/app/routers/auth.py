from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import bearer, get_current_user
from ..models import RevokedToken, User
from ..ratelimit import rate_limit
from ..schemas import LoginIn, RegisterIn
from ..security import create_token, decode_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_HASH = hash_password("dummy-password-1")


def _user_out(u: User) -> dict:
    return {
        "user_id": u.user_id,
        "username": u.username,
        "email": u.email,
    }


@router.post(
    "/register",
    status_code=201,
    dependencies=[Depends(rate_limit("register", 10))],
)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()

    taken = db.scalar(
        select(User).where(
            or_(User.username == body.username, User.email == email)
        )
    )

    if taken:
        raise HTTPException(409, "Username or email already registered")

    user = User(
        username=body.username,
        email=email,
        password_hash=hash_password(body.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username or email already registered")

    return {
        "user_id": user.user_id,
        "message": "User registered",
    }


@router.post(
    "/login",
    dependencies=[Depends(rate_limit("login", 5))],
)
def login(body: LoginIn, db: Session = Depends(get_db)):
    ident = body.identifier.strip()

    user = db.scalar(
        select(User).where(
            or_(
                User.username == ident,
                User.email == ident.lower(),
            )
        )
    )

    ok = verify_password(
        body.password,
        user.password_hash if user else _DUMMY_HASH,
    )

    if not user or not ok:
        raise HTTPException(401, "Invalid credentials")

    return {
        "access_token": create_token(user.user_id),
        "token_type": "bearer",
        "user": _user_out(user),
    }


@router.post("/logout")
def logout(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = decode_token(creds.credentials)

    db.add(
        RevokedToken(
            jti=p["jti"],
            expires_at=datetime.fromtimestamp(
                p["exp"], timezone.utc
            ).replace(tzinfo=None),
        )
    )

    db.commit()

    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)