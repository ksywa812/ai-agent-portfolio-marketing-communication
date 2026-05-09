from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from ai_agent.agent.registry import ToolNotFoundError, ToolRegistry
from ai_agent.tools.base import ToolDefinition


class _AddInput(BaseModel):
    a: int
    b: int


def _add(a: int, b: int) -> dict[str, Any]:
    return {"result": a + b}


_ADD_TOOL = ToolDefinition(
    name="math__add",
    description="Add two numbers",
    input_schema=_AddInput,
    fn=_add,
)


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(_ADD_TOOL)
    return reg


def test_register_and_get(registry: ToolRegistry) -> None:
    tool = registry.get("math__add")
    assert tool.name == "math__add"


def test_get_not_found(registry: ToolRegistry) -> None:
    with pytest.raises(ToolNotFoundError):
        registry.get("nonexistent")


def test_names(registry: ToolRegistry) -> None:
    assert "math__add" in registry.names


def test_call_returns_result(registry: ToolRegistry) -> None:
    result = registry.call("math__add", {"a": 3, "b": 4})
    assert result == {"result": 7}


def test_call_validates_input(registry: ToolRegistry) -> None:
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        registry.call("math__add", {"a": "not_a_number", "b": 4})


def test_call_missing_required_field(registry: ToolRegistry) -> None:
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        registry.call("math__add", {"a": 1})


def test_to_anthropic_format(registry: ToolRegistry) -> None:
    schemas = registry.to_anthropic_format()
    assert len(schemas) == 1
    schema = schemas[0]
    assert schema["name"] == "math__add"
    assert "description" in schema
    assert schema["input_schema"]["type"] == "object"
    assert "a" in schema["input_schema"]["properties"]
    assert "b" in schema["input_schema"]["properties"]
    assert set(schema["input_schema"]["required"]) == {"a", "b"}


def test_register_many() -> None:
    reg = ToolRegistry()
    reg.register_many([_ADD_TOOL, _ADD_TOOL])  # duplicate name — last wins
    assert len(reg.names) == 1
