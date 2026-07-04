"""Schemas for the leaderboard (bonus)."""

from pydantic import BaseModel

from app.schemas.common import PageMeta


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int


class PaginatedLeaderboard(BaseModel):
    data: list[LeaderboardEntry]
    meta: PageMeta
