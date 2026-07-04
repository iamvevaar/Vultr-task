"""
Security primitives: password hashing and JWT tokens.

Two responsibilities, kept small and pure so they're easy to test and explain:
  - hashing/verifying passwords with bcrypt
  - creating/decoding JWT access tokens
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# --- Passwords ---------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """
    Turn a plaintext password into a bcrypt hash for storage.
    bcrypt.gensalt() creates a random salt, so two users with the same password
    get different hashes. We decode to str because the DB column is text.
    """
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Check a login attempt against the stored hash. bcrypt re-derives the hash
    using the salt embedded in `password_hash` and compares in constant time.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


# --- JWT tokens --------------------------------------------------------------

def create_access_token(subject: str, role: str) -> str:
    """
    Build a signed JWT. The payload ("claims") carries:
      sub  - the subject = the user's id (who this token is for)
      role - the user's role, so we can authorize without a DB hit if we want
      iat  - issued-at time
      exp  - expiry time; PyJWT rejects the token automatically after this
    Signed with our secret so nobody can forge or tamper with it.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Verify the signature + expiry and return the claims. Raises a
    jwt.PyJWTError subclass if the token is invalid, tampered, or expired —
    the caller turns that into a 401.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
