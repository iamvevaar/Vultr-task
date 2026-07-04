"""
The Challenge model — a data-driven config, not code.

An admin POSTs a config object; the engine (P5) evaluates ALL challenges from
that config generically. The two flexible parts are JSONB blobs:

  rule_config : the parameters the evaluator reads.
                count  -> {"target": 5}     (do event_type 5 times)
                streak -> {"days": 7}       (do event_type 7 days in a row)
  reward      : what to grant on completion.
                {"type": "points", "amount": 100}
                {"type": "badge", "code": "streak_master", "label": "Streak Master"}

Because these are JSONB, adding a new challenge type or reward type NEVER needs a
schema change — that's what "data-driven" buys us.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChallengeType(str, enum.Enum):
    count = "count"      # complete event_type N times within the window
    streak = "streak"    # complete event_type on N consecutive days


class ChallengeStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    expired = "expired"
    archived = "archived"


class ChallengeCadence(str, enum.Enum):
    one_off = "one_off"
    weekly = "weekly"    # the "weekly challenge" widget uses this


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    type: Mapped[ChallengeType] = mapped_column(
        Enum(ChallengeType, name="challenge_type"), nullable=False
    )
    rule_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Which event this challenge listens to (e.g. "comment_posted").
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reward: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    cadence: Mapped[ChallengeCadence] = mapped_column(
        Enum(ChallengeCadence, name="challenge_cadence"),
        default=ChallengeCadence.one_off,
        nullable=False,
    )
    status: Mapped[ChallengeStatus] = mapped_column(
        Enum(ChallengeStatus, name="challenge_status"),
        default=ChallengeStatus.draft,
        nullable=False,
        index=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
