"""
ChallengeProgress — one row per (challenge, user) tracking how far along they are.

The worker upserts this as events arrive. current_value is whatever the
evaluator computed (a count, or a streak length); state flips to completed when
the target is met. The UNIQUE(challenge_id, user_id) constraint guarantees a
user has exactly one progress row per challenge.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProgressState(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"


class ChallengeProgress(Base):
    __tablename__ = "challenge_progress"
    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uq_progress_challenge_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    challenge_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("challenges.id"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # The evaluator's latest number: count so far, or current streak length.
    current_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    state: Mapped[ProgressState] = mapped_column(
        Enum(ProgressState, name="progress_state"),
        default=ProgressState.in_progress,
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
