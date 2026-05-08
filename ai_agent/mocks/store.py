from __future__ import annotations

from dataclasses import dataclass

from .base import ErrorInjectionConfig
from .calendar import CalendarMock
from .email import EmailMock
from .jira import JiraMock
from .slack import SlackMock


@dataclass
class MockStore:
    slack: SlackMock
    calendar: CalendarMock
    jira: JiraMock
    email: EmailMock

    @classmethod
    def create(
        cls,
        slack_force_error: str | None = None,
        calendar_force_error: str | None = None,
        jira_force_error: str | None = None,
        email_force_error: str | None = None,
    ) -> MockStore:
        def _cfg(mode: str | None) -> ErrorInjectionConfig:
            return ErrorInjectionConfig(force_error=mode)  # type: ignore[arg-type]

        return cls(
            slack=SlackMock(error_config=_cfg(slack_force_error)),
            calendar=CalendarMock(error_config=_cfg(calendar_force_error)),
            jira=JiraMock(error_config=_cfg(jira_force_error)),
            email=EmailMock(error_config=_cfg(email_force_error)),
        )
