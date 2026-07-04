"""
User-facing challenge reads (mounted under /api):

  GET /challenges          active challenges + the caller's progress
  GET /challenges/weekly   the current weekly challenge + progress (or null)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.challenge import Challenge, ChallengeCadence, ChallengeStatus
from app.models.progress import ChallengeProgress
from app.models.user import User
from app.schemas.challenge import ChallengeWithProgress

router = APIRouter(prefix="/challenges", tags=["challenges"])


def _progress_map(db: Session, user_id: int, challenge_ids: list[int]) -> dict[int, ChallengeProgress]:
    """Fetch the user's progress for many challenges in ONE query (avoids N+1)."""
    if not challenge_ids:
        return {}
    rows = db.scalars(
        select(ChallengeProgress).where(
            ChallengeProgress.user_id == user_id,
            ChallengeProgress.challenge_id.in_(challenge_ids),
        )
    ).all()
    return {p.challenge_id: p for p in rows}


@router.get("", response_model=list[ChallengeWithProgress])
def list_active_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    challenges = db.scalars(
        select(Challenge)
        .where(
            Challenge.status == ChallengeStatus.active,
            Challenge.start_at <= now,
            Challenge.end_at >= now,
        )
        .order_by(Challenge.start_at.desc())
    ).all()

    pmap = _progress_map(db, current_user.id, [c.id for c in challenges])
    return [ChallengeWithProgress.from_models(c, pmap.get(c.id)) for c in challenges]


@router.get("/weekly", response_model=ChallengeWithProgress | None)
def weekly_challenge(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    challenge = db.scalar(
        select(Challenge)
        .where(
            Challenge.cadence == ChallengeCadence.weekly,
            Challenge.status == ChallengeStatus.active,
            Challenge.start_at <= now,
            Challenge.end_at >= now,
        )
        .order_by(Challenge.start_at.desc())
        .limit(1)
    )
    if challenge is None:
        return None  # no weekly challenge running right now

    progress = db.scalar(
        select(ChallengeProgress).where(
            ChallengeProgress.user_id == current_user.id,
            ChallengeProgress.challenge_id == challenge.id,
        )
    )
    return ChallengeWithProgress.from_models(challenge, progress)
