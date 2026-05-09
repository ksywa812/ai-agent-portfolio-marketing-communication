from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..mocks.slack import SlackMock
from .base import ToolDefinition


class SendMessageInput(BaseModel):
    channel: str = Field(..., description="Channel name, e.g. #engineering or engineering")
    text: str = Field(..., description="Message text to send")


class ListChannelsInput(BaseModel):
    pass


class SearchMessagesInput(BaseModel):
    query: str = Field(..., description="Text to search for in messages")


def make_slack_tools(mock: SlackMock) -> list[ToolDefinition]:
    def send_message(channel: str, text: str) -> dict[str, Any]:
        return mock.send_message(channel=channel, text=text)

    def list_channels() -> dict[str, Any]:
        return mock.list_channels()

    def search_messages(query: str) -> dict[str, Any]:
        return mock.search_messages(query=query)

    return [
        ToolDefinition(
            name="slack__send_message",
            description=(
                "Send a message to a Slack channel. "
                "Use this when the user asks to post, notify, or message a channel."
            ),
            input_schema=SendMessageInput,
            fn=send_message,
        ),
        ToolDefinition(
            name="slack__list_channels",
            description="List all available Slack channels.",
            input_schema=ListChannelsInput,
            fn=list_channels,
        ),
        ToolDefinition(
            name="slack__search_messages",
            description="Search Slack message history by keyword.",
            input_schema=SearchMessagesInput,
            fn=search_messages,
        ),
    ]
