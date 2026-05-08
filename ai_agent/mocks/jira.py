from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from .base import BaseMock, ErrorInjectionConfig

IssueStatus = Literal["todo", "in_progress", "done"]

_VALID_TRANSITIONS: dict[str, list[str]] = {
    "todo": ["in_progress"],
    "in_progress": ["todo", "done"],
    "done": ["in_progress"],
}


@dataclass
class JiraIssue:
    id: str
    key: str
    title: str
    description: str
    status: IssueStatus
    assignee: str | None
    reporter: str
    project: str
    created: str


class JiraMock(BaseMock):
    def __init__(self, error_config: ErrorInjectionConfig | None = None) -> None:
        super().__init__(error_config)
        self._issues: dict[str, JiraIssue] = {}
        self._counters: dict[str, int] = {}

    def _next_key(self, project: str) -> str:
        self._counters[project] = self._counters.get(project, 0) + 1
        return f"{project}-{self._counters[project]}"

    def create_issue(
        self,
        title: str,
        description: str = "",
        project: str = "PROJ",
        reporter: str = "bot",
    ) -> dict[str, Any]:
        self._check_errors()
        if not title:
            return {"ok": False, "error": "missing_title"}
        key = self._next_key(project)
        issue = JiraIssue(
            id=f"issue_{uuid.uuid4().hex[:8]}",
            key=key,
            title=title,
            description=description,
            status="todo",
            assignee=None,
            reporter=reporter,
            project=project,
            created=datetime.now(timezone.utc).isoformat(),
        )
        self._issues[key] = issue
        return {
            "ok": True,
            "id": issue.id,
            "key": key,
            "title": title,
            "status": "todo",
            "url": f"https://jira.example.com/browse/{key}",
        }

    def get_issue(self, key: str) -> dict[str, Any]:
        self._check_errors()
        issue = self._issues.get(key.upper())
        if not issue:
            return {"ok": False, "error": f"issue_not_found: {key}"}
        return {
            "ok": True,
            "id": issue.id,
            "key": issue.key,
            "title": issue.title,
            "description": issue.description,
            "status": issue.status,
            "assignee": issue.assignee,
            "reporter": issue.reporter,
            "created": issue.created,
            "url": f"https://jira.example.com/browse/{issue.key}",
        }

    def transition_issue(
        self, key: str, status: str, assignee: str | None = None
    ) -> dict[str, Any]:
        self._check_errors()
        issue = self._issues.get(key.upper())
        if not issue:
            return {"ok": False, "error": f"issue_not_found: {key}"}
        valid = _VALID_TRANSITIONS.get(issue.status, [])
        if status not in valid:
            return {
                "ok": False,
                "error": f"invalid_transition: {issue.status} -> {status}. valid: {valid}",
            }
        issue.status = status  # type: ignore[assignment]
        if assignee is not None:
            issue.assignee = assignee
        return {"ok": True, "key": key, "status": status, "assignee": issue.assignee}

    def assign_issue(self, key: str, assignee: str) -> dict[str, Any]:
        self._check_errors()
        issue = self._issues.get(key.upper())
        if not issue:
            return {"ok": False, "error": f"issue_not_found: {key}"}
        issue.assignee = assignee
        return {"ok": True, "key": key, "assignee": assignee}
