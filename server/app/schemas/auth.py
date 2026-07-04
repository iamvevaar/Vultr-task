"""
Pydantic schemas for auth.

Schemas are the API's contract + input validation ("Validate all inputs"):
  - Request schemas reject bad input BEFORE it reaches our logic.
  - Response schemas control exactly what we send back (e.g. never the password
    hash).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr                                  # must be a valid email
    username: str = Field(min_length=3, max_length=50)
    # bcrypt only uses the first 72 bytes, so we cap length there. min 8 = basic strength.
    password: str = Field(min_length=8, max_length=72)
    # Optional: supply the admin code to be created as an admin.
    admin_code: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """What we expose about a user. Note: no password_hash here, ever."""
    id: int
    email: EmailStr
    username: str
    role: UserRole
    created_at: datetime

    # from_attributes lets us build this straight from a SQLAlchemy User object
    # (UserOut.model_validate(user)) instead of a dict.
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
