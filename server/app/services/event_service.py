"""
Event recording — the one idempotent path for creating events.

Both the public POST /events endpoint AND (later) the forum's internal event
emission call record_event(). Centralising it means idempotency is guaranteed
in exactly one place.

Idempotency has two layers:
  1. Fast path: look up the event_id; if we've seen it, return the original
     response and do nothing else.
  2. Safety net: even if two identical requests race past step 1 at the same
     instant, the UNIQUE constraint on events.event_id makes the second INSERT
     fail. We catch that, roll back, and return the winner's stored response.
The database constraint — not the Python check — is the real guarantee.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus


def _accepted_body(event_id: str, event_type: str) -> dict[str, Any]:
    """The canonical 202 body. Built once so the stored snapshot and the live
    response are always identical."""
    return {"event_id": event_id, "event_type": event_type, "status": "accepted"}


def record_event(
    db: Session,
    *,
    event_id: str,
    user_id: int,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> tuple[Event, bool]:
    """
    Store an event exactly once.

    Returns (event, created):
      created=True  -> a new event row was inserted (first time we saw event_id)
      created=False -> this event_id already existed; nothing was reprocessed
    """
    # Layer 1: have we already recorded this event_id?
    existing = db.scalar(select(Event).where(Event.event_id == event_id))
    if existing is not None:
        return existing, False

    event = Event(
        event_id=event_id,
        user_id=user_id,
        event_type=event_type,
        payload=payload or {},
        status=EventStatus.pending,  # the worker will evaluate it later
        response_snapshot=_accepted_body(event_id, event_type),
    )
    db.add(event)

    try:
        db.commit()
    except IntegrityError:
        # Layer 2: a concurrent request won the race and inserted the same
        # event_id microseconds earlier. Roll back our failed insert and return
        # the row that actually landed.
        db.rollback()
        existing = db.scalar(select(Event).where(Event.event_id == event_id))
        return existing, False

    db.refresh(event)
    return event, True
