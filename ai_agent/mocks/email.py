from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from .base import BaseMock, ErrorInjectionConfig

Folder = Literal["sent", "inbox"]


@dataclass
class EmailMessage:
    id: str
    to: list[str]
    subject: str
    body: str
    sender: str
    timestamp: str
    folder: Folder


class EmailMock(BaseMock):
    def __init__(self, error_config: ErrorInjectionConfig | None = None) -> None:
        super().__init__(error_config)
        self._messages: list[EmailMessage] = []

    def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        sender: str = "bot@example.com",
    ) -> dict[str, Any]:
        self._check_errors()
        if not to:
            return {"ok": False, "error": "missing_recipients"}
        if not subject:
            return {"ok": False, "error": "missing_subject"}
        msg = EmailMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            to=to,
            subject=subject,
            body=body,
            sender=sender,
            timestamp=datetime.now(timezone.utc).isoformat(),
            folder="sent",
        )
        self._messages.append(msg)
        return {"ok": True, "id": msg.id, "to": to, "subject": subject}

    def search_email(self, query: str, folder: str = "all") -> dict[str, Any]:
        self._check_errors()
        if not query:
            return {"ok": False, "error": "missing_query"}
        results = [
            {
                "id": m.id,
                "to": m.to,
                "subject": m.subject,
                "snippet": m.body[:200],
                "sender": m.sender,
                "timestamp": m.timestamp,
            }
            for m in self._messages
            if (folder == "all" or m.folder == folder)
            and (query.lower() in m.subject.lower() or query.lower() in m.body.lower())
        ]
        return {"ok": True, "messages": results, "total": len(results)}
