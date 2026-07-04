"""
Per-user reads (mounted under /api):

  GET /users/me/progress   all challenge progress for the caller
  GET /users/me/streaks    per-event-type streak summary + activity days
  GET /users/me/rewards    paginated reward ledger
"""

from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.activity import UserDailyActivity
from app.models.challenge import Challenge
from app.models.progress import ChallengeProgress
from app.models.reward import RewardLedger, RewardType, UserPoints
from app.models.user import User
from app.schemas.challenge import ChallengeWithProgress
from app.schemas.common import PageMeta
from app.schemas.reward import PaginatedRewards, RewardBadge, RewardOut
from app.schemas.streak import ActivityDay, StreakOut, StreaksResponse
from app.services.evaluators import current_streak, longest_consecutive_run

router = APIRouter(prefix="/users/me", tags=["me"])


@router.get("/progress", response_model=list[ChallengeWithProgress])
def my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(ChallengeProgress, Challenge)
        .join(Challenge, Challenge.id == ChallengeProgress.challenge_id)
        .where(ChallengeProgress.user_id == current_user.id)
        .order_by(ChallengeProgress.updated_at.desc())
    ).all()
    return [ChallengeWithProgress.from_models(challenge, progress) for progress, challenge in rows]


@router.get("/streaks", response_model=StreaksResponse)
def my_streaks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(UserDailyActivity.event_type, UserDailyActivity.activity_date)
        .where(UserDailyActivity.user_id == current_user.id)
    ).all()

    # Group active days by event_type.
    by_type: dict[str, set] = defaultdict(set)
    for event_type, day in rows:
        by_type[event_type].add(day)

    today = datetime.now(ZoneInfo(settings.app_tz)).date()

    streaks = [
        StreakOut(
            event_type=event_type,
            current_streak=current_streak(days, today),
            longest_streak=longest_consecutive_run(days),
            last_active_date=max(days),
        )
        for event_type, days in by_type.items()
    ]
    streaks.sort(key=lambda s: s.event_type)

    activity = [
        ActivityDay(date=day, event_type=event_type)
        for event_type, days in by_type.items()
        for day in days
    ]
    activity.sort(key=lambda a: (a.date, a.event_type))

    return StreaksResponse(streaks=streaks, activity=activity)


@router.get("/rewards", response_model=PaginatedRewards)
def my_rewards(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count()).select_from(RewardLedger).where(RewardLedger.user_id == current_user.id)
    ) or 0

    rows = db.execute(
        select(RewardLedger, Challenge.name)
        .join(Challenge, Challenge.id == RewardLedger.source_challenge_id)
        .where(RewardLedger.user_id == current_user.id)
        .order_by(RewardLedger.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    data = [
        RewardOut(
            id=r.id,
            reward_type=r.reward_type,
            amount=r.amount,
            badge_code=r.badge_code,
            label=r.label,
            source_challenge_id=r.source_challenge_id,
            challenge_name=name,
            created_at=r.created_at,
        )
        for r, name in rows
    ]
    pages = (total + limit - 1) // limit

    # Profile summary alongside the ledger: the points balance and earned badges.
    # (badges/points span the whole history, not just this page.)
    total_points = db.scalar(
        select(UserPoints.total_points).where(UserPoints.user_id == current_user.id)
    ) or 0

    badge_rows = db.scalars(
        select(RewardLedger)
        .where(RewardLedger.user_id == current_user.id, RewardLedger.reward_type == RewardType.badge)
        .order_by(RewardLedger.created_at)
    ).all()
    seen: set[str] = set()
    badges: list[RewardBadge] = []
    for r in badge_rows:
        if r.badge_code and r.badge_code not in seen:
            seen.add(r.badge_code)
            badges.append(RewardBadge(code=r.badge_code, label=r.label, awarded_at=r.created_at))

    return PaginatedRewards(
        data=data,
        meta=PageMeta(page=page, limit=limit, total=total, pages=pages),
        total_points=total_points,
        badges=badges,
    )
