"""Scenario C — search and aggregation: calendar events + free slot.

Prompt: 'Show me all my calendar events this week and find a free 2-hour slot for a meeting.'
Expected: calendar__list_events → calendar__find_free_slot → final answer
"""
from __future__ import annotations

from ai_agent.agent.loop import AgentLoop
from ai_agent.agent.registry import ToolRegistry
from ai_agent.llm.client import ToolCall
from ai_agent.mocks.store import MockStore
from tests.conftest import MockLLMClient, text_response, tool_response

_PROMPT = "Show me all my calendar events this week and find a free 2-hour slot for a meeting."


def _build(store: MockStore, registry: ToolRegistry) -> AgentLoop:
    llm = MockLLMClient(
        responses=[
            # Step 1: list events this week
            tool_response([
                ToolCall(
                    id="tc1",
                    name="calendar__list_events",
                    input={
                        "start_date": "2026-05-04T00:00:00",
                        "end_date": "2026-05-08T23:59:59",
                    },
                )
            ]),
            # Step 2: find free 2-hour slot
            tool_response([
                ToolCall(
                    id="tc2",
                    name="calendar__find_free_slot",
                    input={
                        "start_date": "2026-05-04T00:00:00",
                        "end_date": "2026-05-08T23:59:59",
                        "duration_hours": 2,
                    },
                )
            ]),
            text_response(
                "You have 4 events this week. The first free 2-hour slot is Monday 09:30–11:30."
            ),
        ]
    )
    return AgentLoop(llm=llm, registry=registry, max_iterations=5, current_user="pawelc")


def test_scenario_c_two_steps(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    result = loop.run(_PROMPT)

    assert not result.reached_limit
    assert len(result.steps) == 2

    tools_called = [s.tool for s in result.steps]
    assert tools_called == ["calendar__list_events", "calendar__find_free_slot"]


def test_scenario_c_events_returned(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    result = loop.run(_PROMPT)

    list_step = result.steps[0]
    assert list_step.output["ok"] is True
    assert list_step.output["total"] == 4  # seeded with 4 events


def test_scenario_c_free_slot_found(seeded_store: MockStore, registry: ToolRegistry) -> None:
    loop = _build(seeded_store, registry)
    result = loop.run(_PROMPT)

    slot_step = result.steps[1]
    assert slot_step.output["ok"] is True
    assert "slot" in slot_step.output

    from datetime import datetime
    start = datetime.fromisoformat(slot_step.output["slot"]["start"])
    end = datetime.fromisoformat(slot_step.output["slot"]["end"])
    duration = (end - start).seconds / 3600
    assert duration == 2.0
