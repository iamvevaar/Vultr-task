"""
Tier 1: pure-function tests for streak logic. No database needed — we just feed
lists of dates in and assert the number that comes out. This is the streak math
that decides whether a "N consecutive days" challenge is complete, so getting it
right matters. Each test documents one rule of the logic.
"""

from datetime import date

from app.services.evaluators import current_streak, longest_consecutive_run


# --- longest_consecutive_run: the "best run ever" used for completion ---------

def test_longest_run_all_consecutive():
    days = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]
    assert longest_consecutive_run(days) == 3


def test_longest_run_picks_the_longest_of_several():
    # Two runs: {1,2} and {5,6,7}. The longest is 3.
    days = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 5), date(2026, 7, 6), date(2026, 7, 7)]
    assert longest_consecutive_run(days) == 3


def test_longest_run_empty_is_zero():
    assert longest_consecutive_run([]) == 0


def test_longest_run_ignores_duplicate_days():
    # Same day twice must not count as a 2-day streak.
    days = [date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 2)]
    assert longest_consecutive_run(days) == 2


def test_longest_run_order_does_not_matter():
    days = [date(2026, 7, 3), date(2026, 7, 1), date(2026, 7, 2)]
    assert longest_consecutive_run(days) == 3


# --- current_streak: the run ending TODAY (0 if you weren't active today) -----

def test_current_streak_ending_today():
    today = date(2026, 7, 4)
    days = [date(2026, 7, 2), date(2026, 7, 3), date(2026, 7, 4)]
    assert current_streak(days, today) == 3


def test_current_streak_zero_if_not_active_today():
    today = date(2026, 7, 4)
    days = [date(2026, 7, 1), date(2026, 7, 2)]  # nothing on the 4th
    assert current_streak(days, today) == 0


def test_current_streak_only_today_is_one():
    today = date(2026, 7, 4)
    assert current_streak([date(2026, 7, 4)], today) == 1
