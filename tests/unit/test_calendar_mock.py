from __future__ import annotations

import pytest

from ai_agent.mocks.base import ErrorInjectionConfig, RateLimitError
from ai_agent.mocks.calendar import CalendarMock


@pytest.fixture
def cal() -> CalendarMock:
    return CalendarMock()


def test_create_event_ok(cal: CalendarMock) -> None:
    result = cal.create_event(
        title="Team sync",
        start="2026-05-08T10:00:00",
        end="2026-05-08T11:00:00",
        attendees=["alice", "bob"],
    )
    assert result["ok"] is True
    assert result["title"] == "Team sync"
    assert "id" in result


def test_create_event_end_before_start(cal: CalendarMock) -> None:
    result = cal.create_event(
        title="Bad event",
        start="2026-05-08T11:00:00",
        end="2026-05-08T10:00:00",
    )
    assert result["ok"] is False
    assert "end_before_start" in result["error"]


def test_create_event_missing_title(cal: CalendarMock) -> None:
    result = cal.create_event(title="", start="2026-05-08T10:00:00", end="2026-05-08T11:00:00")
    assert result["ok"] is False


def test_list_events_returns_created(cal: CalendarMock) -> None:
    cal.create_event("Morning standup", "2026-05-08T09:00:00", "2026-05-08T09:30:00")
    result = cal.list_events("2026-05-08T00:00:00", "2026-05-08T23:59:59")
    assert result["ok"] is True
    assert result["total"] == 1
    assert result["events"][0]["title"] == "Morning standup"


def test_list_events_outside_range(cal: CalendarMock) -> None:
    cal.create_event("Old event", "2026-05-01T09:00:00", "2026-05-01T10:00:00")
    result = cal.list_events("2026-05-08T00:00:00", "2026-05-08T23:59:59")
    assert result["total"] == 0


def test_find_free_slot_empty_calendar(cal: CalendarMock) -> None:
    result = cal.find_free_slot(
        start_date="2026-05-11T00:00:00",  # Monday
        end_date="2026-05-15T23:59:59",
        duration_hours=1,
    )
    assert result["ok"] is True
    assert "slot" in result
    assert result["slot"]["start"] == "2026-05-11T09:00:00"


def test_find_free_slot_blocked_morning(cal: CalendarMock) -> None:
    # Block 09:00-12:00 on Monday
    cal.create_event("Long meeting", "2026-05-11T09:00:00", "2026-05-11T12:00:00")
    result = cal.find_free_slot(
        start_date="2026-05-11T00:00:00",
        end_date="2026-05-11T23:59:59",
        duration_hours=1,
    )
    assert result["ok"] is True
    # Should find slot at 12:00
    assert "12:00" in result["slot"]["start"]


def test_find_free_slot_two_hours(cal: CalendarMock) -> None:
    result = cal.find_free_slot(
        start_date="2026-05-11T00:00:00",
        end_date="2026-05-15T23:59:59",
        duration_hours=2,
    )
    assert result["ok"] is True
    from datetime import datetime
    start = datetime.fromisoformat(result["slot"]["start"])
    end = datetime.fromisoformat(result["slot"]["end"])
    assert (end - start).seconds == 7200  # 2 hours


def test_find_free_slot_skips_weekends(cal: CalendarMock) -> None:
    # Saturday start
    result = cal.find_free_slot(
        start_date="2026-05-09T00:00:00",  # Saturday
        end_date="2026-05-11T23:59:59",    # Monday
        duration_hours=1,
    )
    assert result["ok"] is True
    # Must land on Monday
    from datetime import datetime
    slot_start = datetime.fromisoformat(result["slot"]["start"])
    assert slot_start.weekday() == 0  # Monday


def test_error_injection(cal: CalendarMock) -> None:
    mock = CalendarMock(error_config=ErrorInjectionConfig(force_error="rate_limit"))
    with pytest.raises(RateLimitError):
        mock.list_events("2026-05-08T00:00:00", "2026-05-08T23:59:59")
