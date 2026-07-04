"""
Tier 2: reward disbursal. Prove that a reward is granted AT MOST ONCE per
(user, challenge) — even if the engine calls disburse_reward twice — and that
both reward types behave correctly.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.security import hash_password
from app.models.challenge import (
    Challenge,
    ChallengeCadence,
    ChallengeStatus,
    ChallengeType,
)
from app.models.reward import RewardLedger, UserPoints
from app.models.user import User, UserRole
from app.services.reward_service import disburse_reward


def _make_user(db) -> User:
    user = User(
        email="rewardee@example.com",
        username="rewardee",
        password_hash=hash_password("password123"),
        role=UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_challenge(db, reward: dict, created_by: int) -> Challenge:
    now = datetime.now(timezone.utc)
    challenge = Challenge(
        name="Test Challenge",
        description="",
        type=ChallengeType.count,
        rule_config={"target": 1},
        event_type="comment_posted",
        start_at=now,
        end_at=now + timedelta(days=1),
        reward=reward,
        cadence=ChallengeCadence.one_off,
        status=ChallengeStatus.active,
        created_by=created_by,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def test_points_reward_is_granted_once(db):
    user = _make_user(db)
    challenge = _make_challenge(db, {"type": "points", "amount": 100}, user.id)
    now = datetime.now(timezone.utc)

    # Disburse TWICE — the second call simulates a re-completion / retry.
    disburse_reward(db, challenge, user.id, now)
    db.commit()
    disburse_reward(db, challenge, user.id, now)
    db.commit()

    # ⭐ Ledger has exactly one row...
    ledger_rows = db.scalar(
        select(func.count()).select_from(RewardLedger).where(RewardLedger.user_id == user.id)
    )
    assert ledger_rows == 1

    # ...and points were added once (100, not 200).
    points = db.scalar(select(UserPoints.total_points).where(UserPoints.user_id == user.id))
    assert points == 100


def test_badge_reward_is_recorded_without_points(db):
    user = _make_user(db)
    challenge = _make_challenge(db, {"type": "badge", "code": "star", "label": "Star"}, user.id)

    disburse_reward(db, challenge, user.id, datetime.now(timezone.utc))
    db.commit()

    row = db.scalar(select(RewardLedger).where(RewardLedger.user_id == user.id))
    assert row.reward_type.value == "badge"
    assert row.badge_code == "star"

    # A badge grants no points, so no points row should exist.
    points = db.scalar(select(UserPoints.total_points).where(UserPoints.user_id == user.id))
    assert points is None


def test_two_different_challenges_reward_separately(db):
    user = _make_user(db)
    c1 = _make_challenge(db, {"type": "points", "amount": 30}, user.id)
    c2 = _make_challenge(db, {"type": "points", "amount": 70}, user.id)
    now = datetime.now(timezone.utc)

    disburse_reward(db, c1, user.id, now)
    disburse_reward(db, c2, user.id, now)
    db.commit()

    # Two distinct challenges → two ledger rows and points summed.
    ledger_rows = db.scalar(
        select(func.count()).select_from(RewardLedger).where(RewardLedger.user_id == user.id)
    )
    assert ledger_rows == 2
    points = db.scalar(select(UserPoints.total_points).where(UserPoints.user_id == user.id))
    assert points == 100
