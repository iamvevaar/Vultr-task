"""
Leaderboard (bonus, mounted under /api):

  GET /leaderboard   users ranked by total points, paginated
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.reward import UserPoints
from app.models.user import User, UserRole
from app.schemas.common import PageMeta
from app.schemas.leaderboard import LeaderboardEntry, PaginatedLeaderboard

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard", response_model=PaginatedLeaderboard)
def leaderboard(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Admins provision challenges; they don't play → exclude them from rankings.
    total = db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.user)
    ) or 0

    # Users may not have a points row yet → COALESCE to 0 so everyone is ranked.
    points = func.coalesce(UserPoints.total_points, 0)
    offset = (page - 1) * limit

    rows = db.execute(
        select(User.id, User.username, points.label("total_points"))
        .outerjoin(UserPoints, UserPoints.user_id == User.id)
        .where(User.role == UserRole.user)
        .order_by(points.desc(), User.id.asc())  # ties broken by id
        .offset(offset)
        .limit(limit)
    ).all()

    data = [
        LeaderboardEntry(rank=offset + i + 1, user_id=row.id, username=row.username, total_points=row.total_points)
        for i, row in enumerate(rows)
    ]
    pages = (total + limit - 1) // limit
    return PaginatedLeaderboard(data=data, meta=PageMeta(page=page, limit=limit, total=total, pages=pages))
