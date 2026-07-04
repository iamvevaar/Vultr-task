"""
Reusable request dependencies for authentication & authorization.

These are the enforcement points for two task rules:
  - "All non-auth endpoints require authentication"  -> get_current_user
  - "Admin endpoints return 403 for non-admin"       -> require_admin

Any route that adds `user = Depends(get_current_user)` is now protected. Any
route that adds `admin = Depends(require_admin)` is admin-only.
"""

import uuid

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import forbidden, unauthorized
from app.core.security import AUTH_COOKIE_NAME, decode_token
from app.models.user import User, UserRole

# HTTPBearer reads the "Authorization: Bearer <token>" header. auto_error=False
# means it returns None instead of raising when the header is missing, so WE
# control the error shape (our envelope) instead of FastAPI's default.
bearer_scheme = HTTPBearer(auto_error=False)


def _load_user(db: Session, subject: str | None) -> User | None:
    """Resolve the JWT `sub` (a UUID string) to a User, safely."""
    if not subject:
        return None
    try:
        return db.get(User, uuid.UUID(subject))
    except (ValueError, TypeError):
        return None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Prefer the Authorization header (Swagger/tests); fall back to the httpOnly
    # cookie (the browser frontend). Either proves who you are.
    token = credentials.credentials if credentials else request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        raise unauthorized("Authentication required")

    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        # Covers invalid signature, malformed token, AND expiry.
        raise unauthorized("Invalid or expired token")

    user = _load_user(db, payload.get("sub"))
    if user is None:
        # Token was valid but the user was deleted since it was issued.
        raise unauthorized("User no longer exists")

    return user


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Like get_current_user, but returns None instead of 401 when there's no valid
    token. Used on publicly-readable endpoints (the feed) so guests can browse,
    while logged-in users still get personalized behaviour.
    """
    token = credentials.credentials if credentials else request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return None
    return _load_user(db, payload.get("sub"))


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Depends on get_current_user first (so you must be logged in), then checks
    the role. Non-admins get a 403, exactly as the task requires.
    """
    if current_user.role != UserRole.admin:
        raise forbidden("Admin privileges required")
    return current_user
