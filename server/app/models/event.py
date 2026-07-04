"""
The Event model — the engine's single input.

Every action in the system (a post created, a comment posted, or an external
POST /events) becomes ONE row here. The engine reads these rows; it knows
nothing about where they came from. That's what "decoupled" means in practice.

Two columns carry the idempotency + async design:
  - event_id (UNIQUE)   : the client-generated key. The unique constraint is the
                          hard guarantee that the same event can't be stored twice.
  - status              : pending -> processed/failed. The worker (P5) picks up
                          'pending' rows. Ingestion just writes 'pending' and returns.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventStatus(str, enum.Enum):
    pending = "pending"       # received, not yet evaluated
    processed = "processed"   # the worker has evaluated it
    failed = "failed"         # evaluation raised; kept for inspection/retry


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    # The client-generated idempotency key. UNIQUE = the database itself refuses
    # a second row with the same event_id, no matter how many requests race.
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Who the event belongs to (taken from the auth token, never the client body).
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # Free-form type string (e.g. "post_created"). The engine stays generic — it
    # does NOT hardcode forum event names; challenges reference types by string.
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Arbitrary JSON detail about the event (post id, etc.). JSONB = queryable json.
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Indexed because the worker constantly queries WHERE status = 'pending'.
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"), default=EventStatus.pending, nullable=False, index=True
    )

    # The exact 202 body we returned. On a duplicate submit we replay THIS,
    # so the caller gets an identical response without any reprocessing.
    response_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
