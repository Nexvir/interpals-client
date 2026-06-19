# interpals_client/models/user.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    """
    A user found in search results.

    This is a lightweight model — only the fields extractable from the
    search-result cards are populated. For full profile data use
    :class:`~interpals_client.models.profile.Profile`.
    """

    username: str
    uid: str = ""
    display_name: str = ""
    age: str = ""
    country: str = ""
    city: str = ""
    native_langs: list[str] = field(default_factory=list)
    learning_langs: list[str] = field(default_factory=list)
    snippet: str = ""               # short bio excerpt

    def __post_init__(self) -> None:
        if not self.display_name:
            self.display_name = self.username

    @property
    def profile_url(self) -> str:
        return f"https://interpals.net/{self.username}"

    def __repr__(self) -> str:
        return (
            f"<User {self.username!r} age={self.age} "
            f"country={self.country!r} native={self.native_langs}>"
        )
