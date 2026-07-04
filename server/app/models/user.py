"""
The User model — our first table.

SQLAlchemy 2.0 style: each column is a typed `Mapped[...]` attribute declared
with `mapped_column(...)`. The class attribute names become Python attributes;
`__tablename__` names the actual Postgres table.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    The two roles the task requires. Subclassing `str` means the value is
    literally the string "user"/"admin" — convenient for JSON and JWT claims.
    """
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    # unique=True adds a DB-level uniqueness constraint (two people can't share
    # an email). index=True makes lookups by email/username fast (we query by
    # email on every login).
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # We store ONLY the bcrypt hash, never the raw password.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Stored as a Postgres ENUM type named "user_role". Defaults to "user" so a
    # normal signup can never accidentally become admin.
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.user, nullable=False
    )

    # server_default=func.now() means Postgres itself stamps the creation time,
    # so it's correct even for rows inserted outside the app.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
