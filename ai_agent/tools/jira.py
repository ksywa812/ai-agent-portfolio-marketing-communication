from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..mocks.jira import JiraMock
from .base import ToolDefinition


class CreateIssueInput(BaseModel):
    title: str = Field(..., description="Issue summary / title")
    description: str = Field(default="", description="Detailed description of the issue")
    project: str = Field(default="PROJ", description="Jira project key, e.g. PROJ")
    reporter: str = Field(default="bot", description="Username of the reporter")


class GetIssueInput(BaseModel):
    key: str = Field(..., description="Issue key, e.g. PROJ-1")


class TransitionIssueInput(BaseModel):
    key: str = Field(..., description="Issue key, e.g. PROJ-1")
    status: str = Field(..., description="Target status: todo | in_progress | done")
    assignee: str | None = Field(default=None, description="Assign to this user at the same time")


def make_jira_tools(mock: JiraMock) -> list[ToolDefinition]:
    def create_issue(
        title: str,
        description: str = "",
        project: str = "PROJ",
        reporter: str = "bot",
    ) -> dict[str, Any]:
        return mock.create_issue(
            title=title, description=description, project=project, reporter=reporter
        )

    def get_issue(key: str) -> dict[str, Any]:
        return mock.get_issue(key=key)

    def transition_issue(
        key: str, status: str, assignee: str | None = None
    ) -> dict[str, Any]:
        return mock.transition_issue(key=key, status=status, assignee=assignee)

    return [
        ToolDefinition(
            name="jira__create_issue",
            description="Create a new Jira issue / ticket. Returns the issue key and URL.",
            input_schema=CreateIssueInput,
            fn=create_issue,
        ),
        ToolDefinition(
            name="jira__get_issue",
            description="Fetch details of a Jira issue by its key, e.g. PROJ-1.",
            input_schema=GetIssueInput,
            fn=get_issue,
        ),
        ToolDefinition(
            name="jira__transition_issue",
            description=(
                "Change the status of a Jira issue and optionally assign it to a user. "
                "Valid statuses: todo, in_progress, done."
            ),
            input_schema=TransitionIssueInput,
            fn=transition_issue,
        ),
    ]
