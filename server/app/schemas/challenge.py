"""
Schemas + validation for challenges.

The tricky part is that rule_config and reward are free-form JSON, but they must
still be VALID for the given type. We validate them with two small pure functions
(normalize_rule_config / normalize_reward) that:
  - apply sensible defaults for missing optional fields, and
  - reject anything malformed with a clear message.
These functions are reused by both create (in a Pydantic validator) and update
(in the route), so the rules live in exactly one place.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.challenge import ChallengeCadence, ChallengeStatus, ChallengeType
from app.models.progress import ProgressState


# --- validation helpers (the heart of "data-driven but validated") ----------

def normalize_rule_config(ctype: ChallengeType, cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Return a clean rule_config for the given type, or raise ValueError."""
    cfg = cfg or {}
    if ctype == ChallengeType.count:
        target = cfg.get("target", 1)  # sensible default
        # bool is a subclass of int, so exclude it explicitly.
        if not isinstance(target, int) or isinstance(target, bool) or target < 1:
            raise ValueError("rule_config.target must be an integer >= 1")
        return {"target": target}

    if ctype == ChallengeType.streak:
        days = cfg.get("days", 1)  # sensible default
        if not isinstance(days, int) or isinstance(days, bool) or days < 1:
            raise ValueError("rule_config.days must be an integer >= 1")
        return {"days": days}

    raise ValueError(f"Unsupported challenge type: {ctype}")


def normalize_reward(reward: dict[str, Any] | None) -> dict[str, Any]:
    """Return a clean reward object, or raise ValueError. Supports points + badges."""
    if not isinstance(reward, dict):
        raise ValueError("reward must be an object")

    rtype = reward.get("type")
    if rtype == "points":
        amount = reward.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
            raise ValueError("points reward requires an integer 'amount' >= 1")
        return {"type": "points", "amount": amount}

    if rtype == "badge":
        code = reward.get("code")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("badge reward requires a non-empty 'code'")
        return {"type": "badge", "code": code, "label": reward.get("label") or code}

    raise ValueError("reward.type must be 'points' or 'badge'")


# --- request schemas --------------------------------------------------------

class ChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    type: ChallengeType
    rule_config: dict[str, Any] = Field(default_factory=dict)
    event_type: str = Field(min_length=1, max_length=100)
    start_at: datetime
    end_at: datetime
    reward: dict[str, Any]
    cadence: ChallengeCadence = ChallengeCadence.one_off
    status: ChallengeStatus = ChallengeStatus.draft

    @model_validator(mode="after")
    def _validate(self):
        # Raising ValueError here becomes a 422 via FastAPI's validation handling.
        self.rule_config = normalize_rule_config(self.type, self.rule_config)
        self.reward = normalize_reward(self.reward)
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class ChallengeUpdate(BaseModel):
    """All optional — PATCH updates only the fields provided."""
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    type: ChallengeType | None = None
    rule_config: dict[str, Any] | None = None
    event_type: str | None = Field(default=None, min_length=1, max_length=100)
    start_at: datetime | None = None
    end_at: datetime | None = None
    reward: dict[str, Any] | None = None
    cadence: ChallengeCadence | None = None
    status: ChallengeStatus | None = None


# --- response schema --------------------------------------------------------

class ChallengeOut(BaseModel):
    id: int
    name: str
    description: str
    type: ChallengeType
    rule_config: dict[str, Any]
    event_type: str
    start_at: datetime
    end_at: datetime
    reward: dict[str, Any]
    cadence: ChallengeCadence
    status: ChallengeStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- user-facing: a challenge together with the caller's progress -----------

class ProgressInfo(BaseModel):
    current_value: int
    target: int
    percent: int          # 0..100, capped
    state: ProgressState
    completed_at: datetime | None


class ChallengeWithProgress(BaseModel):
    id: int
    name: str
    description: str
    type: ChallengeType
    event_type: str
    rule_config: dict[str, Any]
    reward: dict[str, Any]
    start_at: datetime
    end_at: datetime
    cadence: ChallengeCadence
    status: ChallengeStatus
    progress: ProgressInfo

    @classmethod
    def from_models(cls, challenge, progress) -> "ChallengeWithProgress":
        """Build from a Challenge + its (optional) ChallengeProgress row.

        The target is derived from the type's rule_config, so the frontend can
        render "3/5" or a ring without knowing the rules. Missing progress = 0.
        """
        if challenge.type == ChallengeType.count:
            target = int(challenge.rule_config.get("target", 1))
        elif challenge.type == ChallengeType.streak:
            target = int(challenge.rule_config.get("days", 1))
        else:
            target = 1

        if progress is not None:
            current = progress.current_value
            info = ProgressInfo(
                current_value=current,
                target=target,
                percent=min(100, round(current / target * 100)) if target else 0,
                state=progress.state,
                completed_at=progress.completed_at,
            )
        else:
            info = ProgressInfo(
                current_value=0, target=target, percent=0,
                state=ProgressState.in_progress, completed_at=None,
            )

        return cls(
            id=challenge.id,
            name=challenge.name,
            description=challenge.description,
            type=challenge.type,
            event_type=challenge.event_type,
            rule_config=challenge.rule_config,
            reward=challenge.reward,
            start_at=challenge.start_at,
            end_at=challenge.end_at,
            cadence=challenge.cadence,
            status=challenge.status,
            progress=info,
        )
