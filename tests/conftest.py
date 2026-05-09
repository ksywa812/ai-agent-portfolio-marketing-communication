from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from ai_agent.agent.registry import ToolRegistry
from ai_agent.llm.client import LLMResponse, ToolCall
from ai_agent.mocks.seed import seed_store
from ai_agent.mocks.store import MockStore
from ai_agent.tools.calendar import make_calendar_tools
from ai_agent.tools.email import make_email_tools
from ai_agent.tools.jira import make_jira_tools
from ai_agent.tools.slack import make_slack_tools


# ---------------------------------------------------------------------------
# Mock store fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_store() -> MockStore:
    """Empty mock store — no channels, events, or issues."""
    return MockStore.create()


@pytest.fixture
def seeded_store() -> MockStore:
    """Mock store pre-populated with demo data."""
    store = MockStore.create()
    seed_store(store)
    return store


# ---------------------------------------------------------------------------
# Registry fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def registry(seeded_store: MockStore) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_many(make_slack_tools(seeded_store.slack))
    reg.register_many(make_calendar_tools(seeded_store.calendar))
    reg.register_many(make_jira_tools(seeded_store.jira))
    reg.register_many(make_email_tools(seeded_store.email))
    return reg


# ---------------------------------------------------------------------------
# Mock LLM client for integration tests
# ---------------------------------------------------------------------------


class MockLLMClient:
    """Scripted LLM that returns pre-defined responses in order.

    Replaces the real AnthropicClient in integration tests so no API key
    or internet connection is required.
    """

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self._call_count = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if self._call_count >= len(self._responses):
            raise AssertionError(
                f"MockLLMClient called {self._call_count + 1} times but only "
                f"{len(self._responses)} response(s) were scripted."
            )
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


def tool_response(tool_calls: list[ToolCall]) -> LLMResponse:
    """Helper — build an LLMResponse that requests tool calls."""
    raw = [
        {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input}
        for tc in tool_calls
    ]
    return LLMResponse(
        content="",
        tool_calls=tool_calls,
        stop_reason="tool_use",
        raw_blocks=raw,
    )


def text_response(text: str) -> LLMResponse:
    """Helper — build a final LLMResponse with no tool calls."""
    return LLMResponse(
        content=text,
        tool_calls=[],
        stop_reason="end_turn",
        raw_blocks=[{"type": "text", "text": text}],
    )
