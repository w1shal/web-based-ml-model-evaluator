from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_auth, get_current_user
from ..models import RevokedToken, User, utcnow
from ..ratelimit import rate_limit
from ..schemas import LoginIn, RegisterIn
from ..security import EXPIRE_MIN, create_token, decode_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])

# Perform a password hash check even when the account does not exist to reduce
# timing differences between unknown-user and wrong-password responses.
_DUMMY_HASH = hash_password("dummy-password-1")


def _user_out(user: User) -> dict:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
    }


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", 10))],
)
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
        ) from None

    return {
        "user_id": user.user_id,
        "message": "User registered",
    }


@router.post(
    "/login",
    dependencies=[Depends(rate_limit("login", 5))],
)
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

    password_is_valid = verify_password(
        body.password,
        user.password_hash if user else _DUMMY_HASH,
    )

    # Do not reveal whether the username/email exists.
    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return {
        "access_token": create_token(user.user_id, minutes=EXPIRE_MIN),
        "token_type": "bearer",
        "expires_in": EXPIRE_MIN * 60,
        "user": _user_out(user),
    }


@router.post("/logout")
def logout(
    auth: tuple[User, dict] = Depends(get_current_auth),
    db: Session = Depends(get_db),
):
    """Revoke the current JWT until its original expiration time."""
    _, claims = auth
    expires_at = datetime.fromtimestamp(
        claims["exp"],
        timezone.utc,
    ).replace(tzinfo=None)

    db.execute(
        delete(RevokedToken).where(RevokedToken.expires_at < utcnow())
    )
    db.add(RevokedToken(jti=claims["jti"], expires_at=expires_at))
    db.commit()

    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
