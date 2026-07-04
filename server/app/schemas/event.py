"""
Pydantic schemas for event ingestion.
"""

from typing import Any

from pydantic import BaseModel, Field


class EventIngest(BaseModel):
    # Client-generated idempotency key. Typically a UUID the client makes once
    # and reuses on retries. Required and non-empty.
    event_id: str = Field(min_length=1, max_length=255)

    # What happened, as a string. Kept generic on purpose.
    event_type: str = Field(min_length=1, max_length=100)

    # Optional extra detail. default_factory=dict gives each request its own {}.
    payload: dict[str, Any] = Field(default_factory=dict)


class EventAccepted(BaseModel):
    """The 202 body. Stored as response_snapshot and replayed on duplicates."""
    event_id: str
    event_type: str
    status: str  # always "accepted" — it means "queued", not "evaluated"
