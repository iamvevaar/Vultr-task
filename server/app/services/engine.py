"""
The engine: what to do with a single event.

process_event() is called by the worker for each pending event. It:
  1. records the day's activity (for streaks + heatmap),
  2. finds every ACTIVE challenge listening to this event's type whose window
     contains the event, and
  3. re-evaluates the user's progress on each and upserts it.

It does NOT commit — the worker owns the transaction so it can process a batch
and isolate failures per-event. Reward disbursal is added in P6, at the marked hook.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.activity import UserDailyActivity
from app.models.challenge import Challenge, ChallengeStatus
from app.models.event import Event
from app.models.progress import ChallengeProgress, ProgressState
from app.services.evaluators import EVALUATORS
from app.services.reward_service import disburse_reward


def _record_daily_activity(db: Session, user_id: int, event_type: str, activity_date) -> None:
    # ON CONFLICT DO NOTHING: a repeat activity on the same day is a no-op, so the
    # table stays a clean set of active days.
    stmt = (
        pg_insert(UserDailyActivity)
        .values(user_id=user_id, event_type=event_type, activity_date=activity_date)
        .on_conflict_do_nothing(index_elements=["user_id", "event_type", "activity_date"])
    )
    db.execute(stmt)


def _upsert_progress(db: Session, challenge: Challenge, user_id: int, result, now: datetime) -> None:
    progress = db.scalar(
        select(ChallengeProgress).where(
            ChallengeProgress.challenge_id == challenge.id,
            ChallengeProgress.user_id == user_id,
        )
    )
    if progress is None:
        progress = ChallengeProgress(
            challenge_id=challenge.id,
            user_id=user_id,
            current_value=result.current_value,
            state=ProgressState.in_progress,
        )
        db.add(progress)
    else:
        progress.current_value = result.current_value

    # Flip to completed exactly once (the first time the target is met).
    if result.completed and progress.state != ProgressState.completed:
        progress.state = ProgressState.completed
        progress.completed_at = now
        # Grant the reward — idempotent, so this is safe even on a re-completion race.
        disburse_reward(db, challenge, user_id, now)


def process_event(db: Session, event: Event, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)

    # The calendar day, in the app's timezone, for streak bookkeeping.
    activity_date = event.created_at.astimezone(ZoneInfo(settings.app_tz)).date()
    _record_daily_activity(db, event.user_id, event.event_type, activity_date)

    # Which challenges care about this event? Active + matching type + in-window.
    challenges = db.scalars(
        select(Challenge).where(
            Challenge.event_type == event.event_type,
            Challenge.status == ChallengeStatus.active,
            Challenge.start_at <= event.created_at,
            Challenge.end_at >= event.created_at,
        )
    ).all()

    for challenge in challenges:
        evaluator = EVALUATORS.get(challenge.type)
        if evaluator is None:
            continue  # unknown type: skip rather than crash the whole event
        result = evaluator(db, challenge, event.user_id)
        _upsert_progress(db, challenge, event.user_id, result, now)
