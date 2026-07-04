"""Schemas for the leaderboard (bonus)."""

import uuid

from pydantic import BaseModel

from app.schemas.common import PageMeta


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    total_points: int


class PaginatedLeaderboard(BaseModel):
    data: list[LeaderboardEntry]
    meta: PageMeta
