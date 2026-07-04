"""
Tier 2: event idempotency. These need a database, so each test takes the `db`
fixture (a clean session). We prove: submitting the same event_id twice creates
exactly ONE row and returns the ORIGINAL response.
"""

from sqlalchemy import func, select

from app.core.security import hash_password
from app.models.event import Event
from app.models.user import User, UserRole
from app.services.event_service import record_event


def _make_user(db) -> User:
    """Helper: insert a user we can attribute events to."""
    user = User(
        email="tester@example.com",
        username="tester",
        password_hash=hash_password("password123"),
        role=UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_first_submit_creates_event(db):
    user = _make_user(db)
    event, created = record_event(
        db, event_id="evt-1", user_id=user.id, event_type="post_created", payload={}
    )
    assert created is True            # a new row was inserted
    assert event.event_id == "evt-1"


def test_duplicate_submit_does_not_create_a_second_row(db):
    user = _make_user(db)

    # First submit.
    record_event(db, event_id="evt-dup", user_id=user.id, event_type="post_created", payload={})
    # Second submit with the SAME event_id.
    _, created_again = record_event(
        db, event_id="evt-dup", user_id=user.id, event_type="post_created", payload={}
    )

    assert created_again is False     # recognised as a duplicate
    count = db.scalar(select(func.count()).select_from(Event).where(Event.event_id == "evt-dup"))
    assert count == 1                 # ⭐ still only ONE row


def test_replay_returns_the_original_response(db):
    user = _make_user(db)
    first, _ = record_event(db, event_id="evt-snap", user_id=user.id, event_type="x", payload={})
    again, created_again = record_event(db, event_id="evt-snap", user_id=user.id, event_type="x", payload={})

    assert created_again is False
    # The stored snapshot is replayed byte-for-byte.
    assert first.response_snapshot == again.response_snapshot
