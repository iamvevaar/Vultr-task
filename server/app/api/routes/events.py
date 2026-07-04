"""
Event ingestion route:  POST /api/events

Returns 202 Accepted — "I've received and queued this event" — NOT "I've
evaluated it". Evaluation happens later in the background worker. This is the
async contract the task requires.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.event import EventAccepted, EventIngest
from app.services.event_service import record_event

router = APIRouter(tags=["events"])


@router.post("/events", response_model=EventAccepted, status_code=status.HTTP_202_ACCEPTED)
def ingest_event(
    body: EventIngest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # user_id comes from the token, never the request body — an event is always
    # attributed to the authenticated caller.
    event, created = record_event(
        db,
        event_id=body.event_id,
        user_id=current_user.id,
        event_type=body.event_type,
        payload=body.payload,
    )

    # Duplicate submit: we still return 202 with the ORIGINAL body, but flag it
    # with a header so clients/tests can observe the replay without changing the
    # response contract.
    if not created:
        response.headers["X-Idempotent-Replay"] = "true"

    # Return the stored snapshot verbatim, so the first response and every replay
    # are byte-for-byte identical.
    return event.response_snapshot
