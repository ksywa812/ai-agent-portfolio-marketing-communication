from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ErrorMode = Literal["rate_limit", "timeout", "server_error"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"

    # Agent behaviour
    agent_max_iterations: int = Field(default=10, ge=1, le=50)

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    # Mock persistence
    mock_persist_state: bool = False

    # Identity
    current_user: str = "pawelc"

    # Error injection: one of: rate_limit | timeout | server_error
    slack_force_error: ErrorMode | None = None
    calendar_force_error: ErrorMode | None = None
    jira_force_error: ErrorMode | None = None
    email_force_error: ErrorMode | None = None
