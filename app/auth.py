import hashlib
import hmac
import os
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from . import models
from .database import get_db

PBKDF2_ITERATIONS = 200_000


class NotAuthenticated(Exception):
    pass


class Forbidden(Exception):
    pass


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}:{dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(":")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(dk.hex(), hash_hex)


def get_current_user(request: Request, db: Session) -> Optional[models.User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(models.User, user_id)


def require_login(request: Request, db: Session = Depends(get_db)) -> models.User:
    user = get_current_user(request, db)
    if not user:
        raise NotAuthenticated()
    request.state.user = user
    return user


def require_role(*roles: str):
    def dependency(request: Request, db: Session = Depends(get_db)) -> models.User:
        user = get_current_user(request, db)
        if not user:
            raise NotAuthenticated()
        request.state.user = user
        if user.role not in roles:
            raise Forbidden()
        return user

    return dependency
