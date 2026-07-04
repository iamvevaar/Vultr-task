"""
The generic challenge engine: one evaluator per TYPE, driven by rule_config.

There is NO per-challenge logic here — only per-type. Each evaluator is handed a
challenge (whatever its config) and a user, and returns how far along that user
is. Adding a new type = add one function + one line in EVALUATORS. No route,
model, or migration change. That is what "data-driven" means in code.

Both evaluators RECOMPUTE from the source of truth (the events / activity tables)
every time. That makes evaluation naturally idempotent: reprocessing the same
event can't double-count, because we never increment — we recount.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import UserDailyActivity
from app.models.challenge import Challenge, ChallengeType
from app.models.event import Event


@dataclass
class EvalResult:
    current_value: int   # count so far, or streak length
    target: int          # the goal, read from rule_config
    completed: bool


def _evaluate_count(db: Session, challenge: Challenge, user_id: int) -> EvalResult:
    """Count how many matching events the user produced inside the window."""
    target = int(challenge.rule_config.get("target", 1))
    count = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(
            Event.user_id == user_id,
            Event.event_type == challenge.event_type,
            Event.created_at >= challenge.start_at,
            Event.created_at <= challenge.end_at,
        )
    ) or 0
    return EvalResult(current_value=count, target=target, completed=count >= target)


def _longest_consecutive_run(days: list[date]) -> int:
    """Longest run of consecutive calendar days in the given list."""
    dayset = set(days)
    best = 0
    for d in dayset:
        # Only start counting from the beginning of a run (no day directly before it).
        if (d - timedelta(days=1)) not in dayset:
            length = 1
            while (d + timedelta(days=length)) in dayset:
                length += 1
            best = max(best, length)
    return best


def _evaluate_streak(db: Session, challenge: Challenge, user_id: int) -> EvalResult:
    """Find the longest consecutive-day activity run within the window."""
    target = int(challenge.rule_config.get("days", 1))
    days = db.scalars(
        select(UserDailyActivity.activity_date).where(
            UserDailyActivity.user_id == user_id,
            UserDailyActivity.event_type == challenge.event_type,
            UserDailyActivity.activity_date >= challenge.start_at.date(),
            UserDailyActivity.activity_date <= challenge.end_at.date(),
        )
    ).all()
    run = _longest_consecutive_run(list(days))
    return EvalResult(current_value=run, target=target, completed=run >= target)


# The registry. The worker looks up the evaluator by the challenge's type.
EVALUATORS = {
    ChallengeType.count: _evaluate_count,
    ChallengeType.streak: _evaluate_streak,
}


# --- public helpers reused by the read endpoints (/users/me/streaks) ---------

def longest_consecutive_run(days) -> int:
    """Public wrapper: longest run of consecutive days in an iterable of dates."""
    return _longest_consecutive_run(list(days))


def current_streak(days, today: date) -> int:
    """Length of the run of consecutive days ending TODAY (0 if not active today)."""
    dayset = set(days)
    if today not in dayset:
        return 0
    length = 1
    while (today - timedelta(days=length)) in dayset:
        length += 1
    return length
