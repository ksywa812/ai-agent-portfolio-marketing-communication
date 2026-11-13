"""Scenario B: multi-step: Jira ticket + assign + Slack notification.

Prompt: 'Create a Jira ticket for the login bug, assign it to me, then notify #backend-team on Slack.'
Expected: jira__create_issue → jira__transition_issue (assign) → slack__send_message
"""
from __future__ import annotations

from ai_agent.agent.loop import AgentLoop
from ai_agent.agent.registry import ToolRegistry
from ai_agent.llm.client import ToolCall
from ai_agent.mocks.store import MockStore
from tests.conftest import MockLLMClient, text_response, tool_response

_PROMPT = "Create a Jira ticket for the login bug, assign it to me, then notify #backend-team on Slack."


def _build(store: MockStore, registry: ToolRegistry) -> AgentLoop:
    llm = MockLLMClient(
        responses=[
            # Step 1: create the ticket
            tool_response([
                ToolCall(
                    id="tc1",
                    name="jira__create_issue",
                    input={"title": "Login bug", "description": "Login bug reported by user", "project": "PROJ"},
                )
            ]),
            # Step 2: assign it (transition to in_progress + set assignee)
            tool_response([
                ToolCall(
                    id="tc2",
                    name="jira__transition_issue",
                    input={"key": "PROJ-4", "status": "in_progress", "assignee": "pawelc"},
                )
            ]),
            # Step 3: notify Slack
            tool_response([
                ToolCall(
                    id="tc3",
                    name="slack__send_message",
                    input={"channel": "#backend-team", "text": "Jira ticket PROJ-4 created for login bug and assigned to pawelc."},
                )
            ]),
            text_response("Done. Created PROJ-4, assigned to you, and notified #backend-team."),
        ]
    )
    return AgentLoop(llm=llm, registry=registry, max_iterations=10, current_user="pawelc")


def test_scenario_b_three_steps(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    result = loop.run(_PROMPT)

    assert not result.reached_limit
    assert len(result.steps) == 3

    tools_called = [s.tool for s in result.steps]
    assert tools_called == ["jira__create_issue", "jira__transition_issue", "slack__send_message"]


def test_scenario_b_jira_ticket_created(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    loop.run(_PROMPT)

    # The seeded store already has 3 issues, new one is PROJ-4
    issue = seeded_store.jira.get_issue("PROJ-4")
    assert issue["ok"] is True
    assert issue["status"] == "in_progress"
    assert issue["assignee"] == "pawelc"


def test_scenario_b_slack_notified(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    loop.run(_PROMPT)

    messages = seeded_store.slack.search_messages("PROJ-4")
    assert messages["total"] >= 1
