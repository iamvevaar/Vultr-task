"""
Admin challenge management (mounted under /api):

  POST   /admin/challenges        create
  GET    /admin/challenges        list (optional ?status= filter)
  PATCH  /admin/challenges/{id}   update
  DELETE /admin/challenges/{id}   archive (soft delete)

Every route depends on require_admin, so a non-admin gets a 403.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.errors import bad_request, not_found
from app.models.challenge import Challenge, ChallengeStatus
from app.models.user import User
from app.schemas.challenge import (
    ChallengeCreate,
    ChallengeOut,
    ChallengeUpdate,
    normalize_reward,
    normalize_rule_config,
)

router = APIRouter(prefix="/admin/challenges", tags=["challenges-admin"])


@router.post("", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED)
def create_challenge(
    body: ChallengeCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # body is already validated + normalized by ChallengeCreate's validator.
    challenge = Challenge(
        name=body.name,
        description=body.description,
        type=body.type,
        rule_config=body.rule_config,
        event_type=body.event_type,
        start_at=body.start_at,
        end_at=body.end_at,
        reward=body.reward,
        cadence=body.cadence,
        status=body.status,
        created_by=admin.id,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return ChallengeOut.model_validate(challenge)


@router.get("", response_model=list[ChallengeOut])
def list_challenges(
    status: ChallengeStatus | None = None,  # optional ?status= filter
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(Challenge)
    if status is not None:
        stmt = stmt.where(Challenge.status == status)
    stmt = stmt.order_by(Challenge.created_at.desc())
    return [ChallengeOut.model_validate(c) for c in db.scalars(stmt).all()]


@router.patch("/{challenge_id}", response_model=ChallengeOut)
def update_challenge(
    challenge_id: uuid.UUID,
    body: ChallengeUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise not_found("Challenge not found")

    # Only touch fields the client actually sent.
    data = body.model_dump(exclude_unset=True)

    for field in ("name", "description", "event_type", "start_at", "end_at", "cadence", "status", "type"):
        if field in data:
            setattr(challenge, field, data[field])

    # If type or rule_config changed, re-validate rule_config against the new type.
    if "rule_config" in data or "type" in data:
        try:
            challenge.rule_config = normalize_rule_config(
                challenge.type, data.get("rule_config", challenge.rule_config)
            )
        except ValueError as exc:
            raise bad_request(str(exc))

    if "reward" in data:
        try:
            challenge.reward = normalize_reward(data["reward"])
        except ValueError as exc:
            raise bad_request(str(exc))

    if challenge.end_at <= challenge.start_at:
        raise bad_request("end_at must be after start_at")

    db.commit()
    db.refresh(challenge)
    return ChallengeOut.model_validate(challenge)


@router.delete("/{challenge_id}", response_model=ChallengeOut)
def archive_challenge(
    challenge_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # DELETE archives rather than hard-deletes, so history/ledger references stay intact.
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise not_found("Challenge not found")
    challenge.status = ChallengeStatus.archived
    db.commit()
    db.refresh(challenge)
    return ChallengeOut.model_validate(challenge)
