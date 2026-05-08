from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .base import BaseMock, ErrorInjectionConfig

_WORKING_START = 9
_WORKING_END = 17


@dataclass
class CalendarEvent:
    id: str
    title: str
    start: datetime
    end: datetime
    attendees: list[str]
    organizer: str


class CalendarMock(BaseMock):
    def __init__(self, error_config: ErrorInjectionConfig | None = None) -> None:
        super().__init__(error_config)
        self._events: list[CalendarEvent] = []

    def create_event(
        self,
        title: str,
        start: str,
        end: str,
        attendees: list[str] | None = None,
        organizer: str = "bot",
    ) -> dict[str, Any]:
        self._check_errors()
        if not title:
            return {"ok": False, "error": "missing_title"}
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if end_dt <= start_dt:
            return {"ok": False, "error": "end_before_start"}
        event = CalendarEvent(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            title=title,
            start=start_dt,
            end=end_dt,
            attendees=attendees or [],
            organizer=organizer,
        )
        self._events.append(event)
        return {
            "ok": True,
            "id": event.id,
            "title": title,
            "start": start,
            "end": end,
            "attendees": event.attendees,
        }

    def list_events(self, start_date: str, end_date: str) -> dict[str, Any]:
        self._check_errors()
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        events = [
            {
                "id": e.id,
                "title": e.title,
                "start": e.start.isoformat(),
                "end": e.end.isoformat(),
                "attendees": e.attendees,
                "organizer": e.organizer,
            }
            for e in self._events
            if start <= e.start <= end
        ]
        return {"ok": True, "events": events, "total": len(events)}

    def find_free_slot(
        self,
        start_date: str,
        end_date: str,
        duration_hours: int = 1,
    ) -> dict[str, Any]:
        self._check_errors()
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        range_events = sorted(
            [e for e in self._events if e.start < end and e.end > start],
            key=lambda e: e.start,
        )

        current = start.replace(hour=_WORKING_START, minute=0, second=0, microsecond=0)

        while current.date() < end.date() or (
            current.date() == end.date() and current.hour < _WORKING_END
        ):
            if current.weekday() >= 5:
                current = (current + timedelta(days=1)).replace(
                    hour=_WORKING_START, minute=0, second=0, microsecond=0
                )
                continue

            slot_end = current + timedelta(hours=duration_hours)
            if slot_end.hour > _WORKING_END or slot_end.date() != current.date():
                current = (current + timedelta(days=1)).replace(
                    hour=_WORKING_START, minute=0, second=0, microsecond=0
                )
                continue

            overlaps = any(
                not (slot_end <= e.start or current >= e.end) for e in range_events
            )
            if not overlaps:
                return {
                    "ok": True,
                    "slot": {"start": current.isoformat(), "end": slot_end.isoformat()},
                }

            current += timedelta(minutes=30)

        return {"ok": False, "error": "no_free_slot_found"}
