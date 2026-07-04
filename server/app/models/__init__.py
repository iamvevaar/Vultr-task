"""
Model registry.

Importing every model here does two jobs:
  1. Gives you one convenient import:  `from app.models import User`
  2. Ensures each model is registered on `Base.metadata` BEFORE Alembic looks at
     it. Alembic autogenerate compares Base.metadata to the real database, so a
     model it never imported is a model it can't see. Add every new model here.
"""

from app.core.database import Base
from app.models.activity import UserDailyActivity
from app.models.challenge import Challenge, ChallengeCadence, ChallengeStatus, ChallengeType
from app.models.event import Event, EventStatus
from app.models.post import Comment, Post
from app.models.progress import ChallengeProgress, ProgressState
from app.models.user import User, UserRole

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Event",
    "EventStatus",
    "Post",
    "Comment",
    "Challenge",
    "ChallengeType",
    "ChallengeStatus",
    "ChallengeCadence",
    "ChallengeProgress",
    "ProgressState",
    "UserDailyActivity",
]
