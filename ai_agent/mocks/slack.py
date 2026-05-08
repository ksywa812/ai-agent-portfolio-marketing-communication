from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .base import BaseMock, ErrorInjectionConfig


@dataclass
class SlackChannel:
    id: str
    name: str
    is_member: bool = True


@dataclass
class SlackMessage:
    ts: str
    text: str
    user: str
    channel: str


class SlackMock(BaseMock):
    def __init__(self, error_config: ErrorInjectionConfig | None = None) -> None:
        super().__init__(error_config)
        self._channels: dict[str, SlackChannel] = {}
        self._messages: list[SlackMessage] = []

    def add_channel(self, channel_id: str, name: str) -> None:
        self._channels[name] = SlackChannel(id=channel_id, name=name)

    def send_message(self, channel: str, text: str, user: str = "bot") -> dict[str, Any]:
        self._check_errors()
        if not text:
            return {"ok": False, "error": "no_text_provided"}
        channel_key = channel.lstrip("#")
        if channel_key not in self._channels:
            return {"ok": False, "error": f"channel_not_found: #{channel_key}"}
        ts = f"{datetime.now(timezone.utc).timestamp():.6f}"
        self._messages.append(SlackMessage(ts=ts, text=text, user=user, channel=f"#{channel_key}"))
        return {"ok": True, "ts": ts, "channel": self._channels[channel_key].id}

    def list_channels(self) -> dict[str, Any]:
        self._check_errors()
        return {
            "ok": True,
            "channels": [
                {"id": ch.id, "name": ch.name, "is_member": ch.is_member}
                for ch in self._channels.values()
            ],
        }

    def search_messages(self, query: str) -> dict[str, Any]:
        self._check_errors()
        if not query:
            return {"ok": False, "error": "missing_query"}
        results = [
            {"ts": m.ts, "text": m.text, "user": m.user, "channel": m.channel}
            for m in self._messages
            if query.lower() in m.text.lower()
        ]
        return {"ok": True, "messages": results, "total": len(results)}
