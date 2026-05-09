from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..mocks.email import EmailMock
from .base import ToolDefinition


class SendEmailInput(BaseModel):
    to: list[str] = Field(..., description="List of recipient email addresses")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body text")
    sender: str = Field(default="bot@example.com", description="Sender email address")


class SearchEmailInput(BaseModel):
    query: str = Field(..., description="Search term to look for in subject or body")
    folder: str = Field(default="all", description="Folder to search: sent | inbox | all")


def make_email_tools(mock: EmailMock) -> list[ToolDefinition]:
    def send_email(
        to: list[str], subject: str, body: str, sender: str = "bot@example.com"
    ) -> dict[str, Any]:
        return mock.send_email(to=to, subject=subject, body=body, sender=sender)

    def search_email(query: str, folder: str = "all") -> dict[str, Any]:
        return mock.search_email(query=query, folder=folder)

    return [
        ToolDefinition(
            name="email__send_email",
            description="Send an email to one or more recipients.",
            input_schema=SendEmailInput,
            fn=send_email,
        ),
        ToolDefinition(
            name="email__search_email",
            description="Search sent or inbox emails by keyword.",
            input_schema=SearchEmailInput,
            fn=search_email,
        ),
    ]
