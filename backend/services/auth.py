"""Company-portal auth only. Clients never authenticate - they're identified purely
by an opaque client token tied to a Lead (see api/client_routes.py)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Header, HTTPException
from passlib.context import CryptContext

from core.config import get_settings
from database.models import User

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired session.") from exc


class CurrentCompanyUser:
    def __init__(self, id: int, email: str, role: str):
        self.id = id
        self.email = email
        self.role = role


def get_current_company_user(authorization: str | None = Header(default=None)) -> CurrentCompanyUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if payload.get("role") != "COMPANY_ADMIN":
        raise HTTPException(status_code=403, detail="Company access required.")
    return CurrentCompanyUser(id=int(payload["sub"]), email=payload["email"], role=payload["role"])
