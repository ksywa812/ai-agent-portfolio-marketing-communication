from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass
class ToolDefinition:
    """A single tool the agent can call.

    ``name`` must be alphanumeric + underscores only — the Anthropic API rejects
    dots and other special characters in tool names.
    Convention: double-underscore separates service from action, e.g. slack__send_message.
    """

    name: str
    description: str
    input_schema: type[BaseModel]
    fn: Callable[..., dict[str, Any]]
