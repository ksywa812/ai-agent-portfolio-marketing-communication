from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from ai_agent.llm.client import LLMClient, ToolCall
# Helpers: fake Anthropic response objects


@dataclass
class _FakeTextBlock:
    type: str = "text"
    text: str = "hello"


@dataclass
class _FakeToolUseBlock:
    type: str = "tool_use"
    id: str = "toolu_01"
    name: str = "slack__send_message"
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class _FakeMessage:
    content: list[Any]
    stop_reason: str = "end_turn"


def _make_client() -> LLMClient:
    return LLMClient(api_key="test-key", model="claude-test", max_retries=3)
# Tests


def test_chat_returns_text_response() -> None:
    client = _make_client()
    fake_msg = _FakeMessage(content=[_FakeTextBlock(text="Done!")])

    with patch.object(client._client.messages, "create", return_value=fake_msg):
        response = client.chat(messages=[], tools=[], system="")

    assert response.content == "Done!"
    assert response.stop_reason == "end_turn"
    assert response.tool_calls == []


def test_chat_parses_tool_calls() -> None:
    client = _make_client()
    fake_msg = _FakeMessage(
        content=[_FakeToolUseBlock(id="tc1", name="slack__send_message", input={"channel": "#eng", "text": "hi"})],
        stop_reason="tool_use",
    )

    with patch.object(client._client.messages, "create", return_value=fake_msg):
        response = client.chat(messages=[], tools=[], system="")

    assert len(response.tool_calls) == 1
    tc = response.tool_calls[0]
    assert tc.id == "tc1"
    assert tc.name == "slack__send_message"
    assert tc.input == {"channel": "#eng", "text": "hi"}
    assert response.stop_reason == "tool_use"


def test_chat_retries_on_rate_limit() -> None:
    client = _make_client()
    fake_msg = _FakeMessage(content=[_FakeTextBlock(text="ok")])
    call_count = 0

    def side_effect(**kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise anthropic.RateLimitError("rate limit", response=MagicMock(), body={})
        return fake_msg

    with patch.object(client._client.messages, "create", side_effect=side_effect):
        with patch("ai_agent.llm.client.time.sleep"):
            response = client.chat(messages=[], tools=[], system="")

    assert response.content == "ok"
    assert call_count == 3


def test_chat_raises_after_max_retries() -> None:
    client = _make_client()

    with patch.object(
        client._client.messages,
        "create",
        side_effect=anthropic.RateLimitError("rate limit", response=MagicMock(), body={}),
    ):
        with patch("ai_agent.llm.client.time.sleep"):
            with pytest.raises(RuntimeError, match="failed after"):
                client.chat(messages=[], tools=[], system="")


def test_chat_does_not_retry_api_error() -> None:
    client = _make_client()
    call_count = 0

    def side_effect(**kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        raise anthropic.BadRequestError("bad request", response=MagicMock(), body={})

    with patch.object(client._client.messages, "create", side_effect=side_effect):
        with pytest.raises(anthropic.BadRequestError):
            client.chat(messages=[], tools=[], system="")

    assert call_count == 1  # no retries
