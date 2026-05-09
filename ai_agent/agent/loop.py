from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import structlog

from ..llm.client import LLMClient
from .prompts import build_system_prompt
from .registry import ToolRegistry

log = structlog.get_logger(__name__)


@dataclass
class Step:
    tool: str
    input: dict[str, Any]
    output: dict[str, Any]


@dataclass
class AgentResult:
    final_answer: str
    steps: list[Step]
    reached_limit: bool = False


class AgentLoop:
    def __init__(
        self,
        llm: LLMClient,
        registry: ToolRegistry,
        max_iterations: int = 10,
        current_user: str = "pawelc",
    ) -> None:
        self._llm = llm
        self._registry = registry
        self._max_iterations = max_iterations
        self._current_user = current_user

    def run(self, user_prompt: str) -> AgentResult:
        system = build_system_prompt(self._current_user)
        tools = self._registry.to_anthropic_format()
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
        steps: list[Step] = []

        log.info("agent_start", prompt=user_prompt[:80])

        for iteration in range(self._max_iterations):
            log.debug("agent_iteration", iteration=iteration + 1)
            response = self._llm.chat(messages=messages, tools=tools, system=system)

            if response.stop_reason == "end_turn" or not response.tool_calls:
                log.info("agent_done", steps=len(steps))
                return AgentResult(final_answer=response.content, steps=steps)

            # Append the assistant message with all tool_use blocks
            messages.append({"role": "assistant", "content": response.raw_blocks})

            # Execute every tool call in this turn (Claude may request several at once)
            tool_results = []
            for tc in response.tool_calls:
                log.info("tool_executing", tool=tc.name, input=tc.input)
                try:
                    result = self._registry.call(tc.name, tc.input)
                except Exception as e:
                    result = {"ok": False, "error": str(e)}
                    log.warning("tool_error", tool=tc.name, error=str(e))

                steps.append(Step(tool=tc.name, input=tc.input, output=result))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

            # Return all results to the LLM in one user message
            messages.append({"role": "user", "content": tool_results})

        log.warning("agent_limit_reached", max_iterations=self._max_iterations)
        return AgentResult(
            final_answer="I reached the maximum number of steps without completing the task. Please try a simpler request or increase the step limit.",
            steps=steps,
            reached_limit=True,
        )
