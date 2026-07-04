"""
Auth routes:  POST /auth/register, POST /auth/login, GET /auth/me
(mounted under /api by main.py, so the full paths are /api/auth/...).
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import conflict, unauthorized
from app.core.security import (
    clear_auth_cookie,
    create_access_token,
    hash_password,
    set_auth_cookie,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    # Reject duplicates up front with a clean 409 instead of relying on a raw
    # DB IntegrityError. The unique constraints on the table are the safety net.
    existing = db.scalar(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing:
        raise conflict("Email or username already registered")

    # Only the correct admin code grants the admin role; everyone else is a user.
    role = (
        UserRole.admin
        if body.admin_code and body.admin_code == settings.admin_signup_code
        else UserRole.user
    )

    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # reload so we get the DB-generated id and created_at

    token = create_access_token(subject=str(user.id), role=user.role.value)
    set_auth_cookie(response, token)  # browser stores the httpOnly cookie
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    # One generic message for "no such user" AND "wrong password" so we don't
    # leak which emails are registered.
    if user is None or not verify_password(body.password, user.password_hash):
        raise unauthorized("Invalid email or password")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    set_auth_cookie(response, token)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(response: Response):
    # Clears the auth cookie. Safe to call even if not logged in.
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    # Protected by get_current_user; returns the caller + their role.
    return UserOut.model_validate(current_user)
