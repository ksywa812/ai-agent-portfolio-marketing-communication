from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import anthropic
import structlog

log = structlog.get_logger(__name__)

_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall]
    stop_reason: str
    raw_blocks: list[Any] = field(default_factory=list)


class LLMClient:
    """Thin wrapper around the Anthropic Messages API with retry and timeout."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self._model = model
        self._max_retries = max_retries

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                log.debug("llm_request", model=self._model, messages=len(messages))
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    system=system,
                    tools=tools,  # type: ignore[arg-type]
                    messages=messages,  # type: ignore[arg-type]
                )
                return self._parse(response)
            except anthropic.RateLimitError as e:
                last_exc = e
                delay = _RETRY_BASE_DELAY * (2**attempt)
                log.warning("llm_rate_limit", attempt=attempt + 1, retry_in=delay)
                time.sleep(delay)
            except anthropic.APITimeoutError as e:
                last_exc = e
                delay = _RETRY_BASE_DELAY * (2**attempt)
                log.warning("llm_timeout", attempt=attempt + 1, retry_in=delay)
                time.sleep(delay)
            except anthropic.APIError as e:
                log.error("llm_api_error", error=str(e))
                raise

        raise RuntimeError(
            f"LLM request failed after {self._max_retries} attempts"
        ) from last_exc

    @staticmethod
    def _parse(response: anthropic.types.Message) -> LLMResponse:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        input=dict(block.input),
                    )
                )

        return LLMResponse(
            content=" ".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
            raw_blocks=list(response.content),
        )
