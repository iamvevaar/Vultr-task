"""Schemas for the user-facing reward ledger."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.reward import RewardType
from app.schemas.common import PageMeta


class RewardOut(BaseModel):
    id: uuid.UUID
    reward_type: RewardType
    amount: int
    badge_code: str | None
    label: str | None
    source_challenge_id: uuid.UUID
    challenge_name: str | None   # joined in for display
    created_at: datetime


class RewardBadge(BaseModel):
    code: str
    label: str | None
    awarded_at: datetime


class PaginatedRewards(BaseModel):
    data: list[RewardOut]
    meta: PageMeta
    total_points: int          # profile summary: current points balance
    badges: list[RewardBadge]  # profile summary: distinct badges earned
