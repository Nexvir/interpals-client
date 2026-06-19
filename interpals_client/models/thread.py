# interpals_client/models/thread.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Thread:
    """An inbox conversation thread."""

    id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    snippet: Optional[str] = None       # last message preview
    has_unread: bool = False
    inactive: bool = False

    def __repr__(self) -> str:
        return f"<Thread id={self.id} username={self.username!r} unread={self.has_unread}>"
