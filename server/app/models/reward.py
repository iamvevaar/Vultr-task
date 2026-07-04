"""
Reward models: the ledger (history) and the points balance (fast lookup).

RewardLedger  - one immutable row per reward ever granted. This is the audit
                trail the task asks for (type, amount, source challenge, time).
                The UNIQUE(user_id, source_challenge_id) constraint is THE
                idempotency guarantee: a challenge can reward a user at most once.

UserPoints    - a denormalized running total, so the profile and leaderboard
                don't have to SUM the whole ledger on every request. Kept in
                sync inside the same transaction that writes the ledger row.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RewardType(str, enum.Enum):
    points = "points"
    badge = "badge"


class RewardLedger(Base):
    __tablename__ = "reward_ledger"
    __table_args__ = (
        # ⭐ idempotent disbursal: one reward per (user, challenge), forever.
        UniqueConstraint("user_id", "source_challenge_id", name="uq_reward_user_challenge"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    source_challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id"), index=True, nullable=False
    )

    reward_type: Mapped[RewardType] = mapped_column(
        Enum(RewardType, name="reward_type"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # points amount (0 for badges)
    badge_code: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "on_fire"
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)       # human-readable

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserPoints(Base):
    __tablename__ = "user_points"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
