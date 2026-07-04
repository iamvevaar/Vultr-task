"""
Reward disbursal — called by the engine exactly at challenge completion.

Idempotency is enforced at the database level:
  - We INSERT the ledger row with ON CONFLICT DO NOTHING on
    (user_id, source_challenge_id). RETURNING id tells us whether a row was
    actually inserted.
  - Points are added to the balance ONLY when a new row was inserted. So even if
    the engine somehow tries to reward the same completion twice (a race, a
    reprocessed event), the second attempt inserts nothing and adds no points.

This does NOT commit — it runs inside the worker's per-event transaction.
"""

from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.challenge import Challenge
from app.models.reward import RewardLedger, RewardType, UserPoints


def _add_points(db: Session, user_id: int, amount: int) -> None:
    """Create or increment the user's points balance, atomically."""
    insert_stmt = pg_insert(UserPoints).values(user_id=user_id, total_points=amount)
    stmt = insert_stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={"total_points": UserPoints.__table__.c.total_points + insert_stmt.excluded.total_points},
    )
    db.execute(stmt)


def disburse_reward(db: Session, challenge: Challenge, user_id: int, now: datetime) -> None:
    reward = challenge.reward or {}
    rtype = reward.get("type")

    if rtype == "points":
        values = dict(
            user_id=user_id,
            source_challenge_id=challenge.id,
            reward_type=RewardType.points,
            amount=int(reward.get("amount", 0)),
        )
    elif rtype == "badge":
        values = dict(
            user_id=user_id,
            source_challenge_id=challenge.id,
            reward_type=RewardType.badge,
            amount=0,
            badge_code=reward.get("code"),
            label=reward.get("label"),
        )
    else:
        return  # unknown reward type — nothing to grant

    # Try to write the ledger row. RETURNING id is None if it already existed.
    stmt = (
        pg_insert(RewardLedger)
        .values(**values)
        .on_conflict_do_nothing(index_elements=["user_id", "source_challenge_id"])
        .returning(RewardLedger.id)
    )
    inserted_id = db.scalar(stmt)

    if inserted_id is None:
        return  # already rewarded for this challenge — idempotent no-op

    # Side effect only on a genuinely new reward: bump the points balance.
    if values["reward_type"] == RewardType.points and values["amount"] > 0:
        _add_points(db, user_id, values["amount"])
