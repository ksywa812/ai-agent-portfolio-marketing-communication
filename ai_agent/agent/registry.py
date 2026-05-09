from __future__ import annotations

from typing import Any

import structlog

from ..tools.base import ToolDefinition

log = structlog.get_logger(__name__)


class ToolNotFoundError(Exception):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool
        log.debug("tool_registered", name=tool.name)

    def register_many(self, tools: list[ToolDefinition]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> ToolDefinition:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"No tool registered with name '{name}'")
        return tool

    def call(self, name: str, raw_input: dict[str, Any]) -> dict[str, Any]:
        """Validate input against the tool's Pydantic schema then invoke it."""
        tool = self.get(name)
        validated = tool.input_schema.model_validate(raw_input)
        log.debug("tool_call", tool=name, input=raw_input)
        result = tool.fn(**validated.model_dump())
        log.debug("tool_result", tool=name, result=result)
        return result

    def to_anthropic_format(self) -> list[dict[str, Any]]:
        """Serialize all registered tools into the Anthropic tool-use schema."""
        result = []
        for tool in self._tools.values():
            schema = tool.input_schema.model_json_schema()
            result.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": {
                        "type": "object",
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", []),
                    },
                }
            )
        return result

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())
