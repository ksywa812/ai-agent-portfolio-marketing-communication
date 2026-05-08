from __future__ import annotations

from datetime import datetime, timedelta

from .store import MockStore

_WEEK_ANCHOR = datetime(2026, 5, 4, 0, 0, 0)  # Monday 2026-05-04


def seed_store(store: MockStore, current_user: str = "pawelc") -> None:
    """Pre-populate all mock stores with realistic demo data."""
    _seed_slack(store)
    _seed_calendar(store, current_user)
    _seed_jira(store, current_user)


def _seed_slack(store: MockStore) -> None:
    store.slack.add_channel("C001", "engineering")
    store.slack.add_channel("C002", "backend-team")
    store.slack.add_channel("C003", "design")
    store.slack.add_channel("C004", "general")


def _seed_calendar(store: MockStore, current_user: str) -> None:
    mon = _WEEK_ANCHOR
    wed = mon + timedelta(days=2)
    thu = mon + timedelta(days=3)

    events = [
        (
            "Team standup",
            mon.replace(hour=9),
            mon.replace(hour=9, minute=30),
            [current_user, "anna", "tomek"],
        ),
        (
            "Sprint planning",
            mon.replace(hour=14),
            mon.replace(hour=16),
            [current_user, "anna"],
        ),
        (
            "1:1 with manager",
            wed.replace(hour=11),
            wed.replace(hour=12),
            [current_user, "manager"],
        ),
        (
            "Architecture review",
            thu.replace(hour=10),
            thu.replace(hour=11, minute=30),
            [current_user, "anna", "tomek", "karol"],
        ),
    ]
    for title, start, end, attendees in events:
        store.calendar.create_event(
            title=title,
            start=start.isoformat(),
            end=end.isoformat(),
            attendees=attendees,
            organizer=current_user,
        )


def _seed_jira(store: MockStore, current_user: str) -> None:
    store.jira.create_issue(
        title="Fix authentication timeout",
        description="Users getting logged out after 10 min of inactivity",
        reporter=current_user,
    )
    store.jira.create_issue(
        title="Migrate to PostgreSQL 16",
        description="DB upgrade planned for Q2 — coordinate with infra team",
        reporter="anna",
    )
    store.jira.create_issue(
        title="Login bug: incorrect error message shown",
        description="When password is wrong the UI shows 'server error' instead of 'invalid credentials'",
        reporter=current_user,
    )
