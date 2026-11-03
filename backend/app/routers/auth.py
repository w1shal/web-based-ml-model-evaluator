from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import RegisterIn
from ..security import hash_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterIn,
    db: Session = Depends(get_db),
):
    normalized_email = str(body.email).lower()

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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    # Never return the password or password hash.
    return {
        "user_id": user.user_id,
        "message": "User registered",
    }
