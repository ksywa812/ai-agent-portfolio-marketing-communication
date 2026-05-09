from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..mocks.calendar import CalendarMock
from .base import ToolDefinition


class CreateEventInput(BaseModel):
    title: str = Field(..., description="Event title")
    start: str = Field(..., description="Start datetime in ISO 8601, e.g. 2026-05-08T14:00:00")
    end: str = Field(..., description="End datetime in ISO 8601, e.g. 2026-05-08T15:00:00")
    attendees: list[str] = Field(default_factory=list, description="List of attendee usernames")


class ListEventsInput(BaseModel):
    start_date: str = Field(..., description="Range start in ISO 8601, e.g. 2026-05-05T00:00:00")
    end_date: str = Field(..., description="Range end in ISO 8601, e.g. 2026-05-09T23:59:59")


class FindFreeSlotInput(BaseModel):
    start_date: str = Field(..., description="Search range start in ISO 8601")
    end_date: str = Field(..., description="Search range end in ISO 8601")
    duration_hours: int = Field(default=1, ge=1, le=8, description="Required slot length in hours")


def make_calendar_tools(mock: CalendarMock) -> list[ToolDefinition]:
    def create_event(
        title: str, start: str, end: str, attendees: list[str] | None = None
    ) -> dict[str, Any]:
        return mock.create_event(title=title, start=start, end=end, attendees=attendees or [])

    def list_events(start_date: str, end_date: str) -> dict[str, Any]:
        return mock.list_events(start_date=start_date, end_date=end_date)

    def find_free_slot(
        start_date: str, end_date: str, duration_hours: int = 1
    ) -> dict[str, Any]:
        return mock.find_free_slot(
            start_date=start_date, end_date=end_date, duration_hours=duration_hours
        )

    return [
        ToolDefinition(
            name="calendar__create_event",
            description=(
                "Create a new Google Calendar event. "
                "Requires title, start and end datetimes in ISO 8601 format."
            ),
            input_schema=CreateEventInput,
            fn=create_event,
        ),
        ToolDefinition(
            name="calendar__list_events",
            description=(
                "List all calendar events within a date range. "
                "Use this to show the user their schedule."
            ),
            input_schema=ListEventsInput,
            fn=list_events,
        ),
        ToolDefinition(
            name="calendar__find_free_slot",
            description=(
                "Find the first available time slot of the requested duration "
                "within working hours (09:00-17:00, Mon-Fri)."
            ),
            input_schema=FindFreeSlotInput,
            fn=find_free_slot,
        ),
    ]
