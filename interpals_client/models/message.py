# interpals_client/models/message.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Author:
    name: str
    id: Optional[str] = None


@dataclass
class Message:
    """A single private message inside a thread."""

    id: str
    content: str
    created_at: str          # ISO 8601
    author: Author
    is_own: bool = False

    def __repr__(self) -> str:
        return f"<Message id={self.id} from={self.author.name!r} content={self.content[:40]!r}>"

    @property
    def age_seconds(self) -> float:
        """Seconds elapsed since the message was sent (approximate, UTC)."""
        try:
            dt = datetime.fromisoformat(self.created_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).total_seconds()
        except Exception:
            return 0.0
