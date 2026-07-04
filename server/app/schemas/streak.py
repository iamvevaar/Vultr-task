"""Schemas for streaks + activity (feeds the streak heatmap on the frontend)."""

from datetime import date

from pydantic import BaseModel


class StreakOut(BaseModel):
    event_type: str
    current_streak: int   # consecutive days ending today
    longest_streak: int   # best run ever
    last_active_date: date


class ActivityDay(BaseModel):
    """One active day for one event type — the heatmap consumes a list of these."""
    date: date
    event_type: str


class StreaksResponse(BaseModel):
    streaks: list[StreakOut]     # per event_type summary
    activity: list[ActivityDay]  # raw days for visualisation
