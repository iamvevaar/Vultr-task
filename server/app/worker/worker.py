"""
The background worker — a separate process (its own container).

It polls the events table forever. Each tick:
  1. SELECT a batch of pending events ... FOR UPDATE SKIP LOCKED
     - FOR UPDATE  : lock these rows so no other worker touches them
     - SKIP LOCKED : if another worker already locked a row, skip it (don't wait)
     -> multiple workers can run safely without ever double-processing an event.
  2. process each event inside its own SAVEPOINT, so one bad event fails alone
     (marked 'failed') instead of poisoning the whole batch.
  3. commit the batch, then sleep only if there was nothing to do.

Run it with:  python -m app.worker.worker   (see docker-compose 'worker' service)
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select

import app.models  # noqa: F401  -- import so every model is registered on the mapper
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.event import Event, EventStatus
from app.services.engine import process_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("worker")

BATCH_SIZE = 20


def run_once() -> int:
    """Process one batch. Returns how many events were handled (0 = idle)."""
    with SessionLocal() as db:
        events = db.scalars(
            select(Event)
            .where(Event.status == EventStatus.pending)
            .order_by(Event.created_at)
            .with_for_update(skip_locked=True)
            .limit(BATCH_SIZE)
        ).all()

        if not events:
            return 0

        now = datetime.now(timezone.utc)
        for event in events:
            savepoint = db.begin_nested()  # SAVEPOINT for this one event
            try:
                process_event(db, event, now)
                event.status = EventStatus.processed
                event.processed_at = now
                savepoint.commit()
            except Exception:
                savepoint.rollback()  # undo this event's partial changes only
                logger.exception("failed to process event %s", event.event_id)
                event.status = EventStatus.failed

        db.commit()  # releases the row locks
        logger.info("processed %d event(s)", len(events))
        return len(events)


def main() -> None:
    logger.info("worker started (poll=%ss, batch=%s)", settings.worker_poll_seconds, BATCH_SIZE)
    while True:
        try:
            handled = run_once()
        except Exception:
            logger.exception("worker loop error")
            handled = 0
        # If we did work, loop immediately to drain the backlog; otherwise wait.
        if handled == 0:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
