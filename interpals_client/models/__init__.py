# interpals_client/models/__init__.py
"""Data models returned by interpals-client."""

from .message import Author, Message
from .thread import Thread
from .user import User
from .profile import Profile

__all__ = ["Author", "Message", "Thread", "User", "Profile"]
