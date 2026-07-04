"""
UserDailyActivity — a set of (user, event_type, day) rows.

One row means "this user did this event_type at least once on this calendar day
(in APP_TZ)". It's deliberately a SET, not a counter: the UNIQUE constraint means
five comments on the same day still produce ONE row.

This table powers two things:
  - streak evaluation  (longest run of consecutive activity_date values)
  - the streak heatmap on the frontend (a value per day)
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserDailyActivity(Base):
    __tablename__ = "user_daily_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "event_type", "activity_date", name="uq_activity_user_type_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
