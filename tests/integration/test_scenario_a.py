"""Scenario A — simple Slack message send.

Prompt: 'Send a message to #engineering: Deployment of v2.4.1 completed successfully.'
Expected: agent calls slack__send_message with correct parameters.
"""
from __future__ import annotations

from ai_agent.agent.loop import AgentLoop
from ai_agent.agent.registry import ToolRegistry
from ai_agent.llm.client import ToolCall
from ai_agent.mocks.seed import seed_store
from ai_agent.mocks.store import MockStore
from ai_agent.tools.slack import make_slack_tools
from tests.conftest import MockLLMClient, text_response, tool_response


def _build(store: MockStore, registry: ToolRegistry) -> AgentLoop:
    llm = MockLLMClient(
        responses=[
            tool_response([
                ToolCall(
                    id="tc1",
                    name="slack__send_message",
                    input={"channel": "#engineering", "text": "Deployment of v2.4.1 completed successfully."},
                )
            ]),
            text_response("Message sent to #engineering successfully."),
        ]
    )
    return AgentLoop(llm=llm, registry=registry, max_iterations=5, current_user="pawelc")


def test_scenario_a_sends_message(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    result = loop.run("Send a message to #engineering: Deployment of v2.4.1 completed successfully.")

    assert not result.reached_limit
    assert len(result.steps) == 1

    step = result.steps[0]
    assert step.tool == "slack__send_message"
    assert step.input["channel"] == "#engineering"
    assert "v2.4.1" in step.input["text"]
    assert step.output["ok"] is True


def test_scenario_a_message_visible_in_search(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    loop.run("Send a message to #engineering: Deployment of v2.4.1 completed successfully.")

    # Message must be retrievable — proves state persists
    search = seeded_store.slack.search_messages("v2.4.1")
    assert search["total"] == 1
    assert "v2.4.1" in search["messages"][0]["text"]
