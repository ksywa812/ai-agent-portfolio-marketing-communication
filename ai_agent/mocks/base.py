from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

ErrorMode = Literal["rate_limit", "timeout", "server_error"]


class MockError(Exception):
    pass


class RateLimitError(MockError):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message)


class TimeoutError(MockError):
    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)


class ServerError(MockError):
    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message)


@dataclass
class ErrorInjectionConfig:
    force_error: ErrorMode | None = None
    error_rate: float = field(default=0.0)


class BaseMock:
    def __init__(self, error_config: ErrorInjectionConfig | None = None) -> None:
        self._error_config = error_config or ErrorInjectionConfig()

    def _check_errors(self) -> None:
        mode = self._error_config.force_error
        if mode == "rate_limit":
            raise RateLimitError()
        if mode == "timeout":
            raise TimeoutError()
        if mode == "server_error":
            raise ServerError()
        if self._error_config.error_rate > 0 and random.random() < self._error_config.error_rate:
            raise ServerError("Random error injection triggered")
