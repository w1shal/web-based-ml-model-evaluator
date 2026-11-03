import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import RevokedToken, User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def _resolve(creds, db):
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    if db.get(RevokedToken, payload["jti"]):
        raise HTTPException(401, "Token has been revoked")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "Invalid token")
    return user


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise HTTPException(401, "Not authenticated")
    return _resolve(creds, db)


def get_optional_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                      db: Session = Depends(get_db)):
    """For guest-friendly endpoints (upload/evaluate): None means guest."""
    return _resolve(creds, db) if creds else None
