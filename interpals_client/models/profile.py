# interpals_client/models/profile.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    """
    Full profile data parsed from a user's profile page.

    This is a superset of :class:`~interpals_client.models.user.User` —
    it includes the same fields plus bio, languages at a finer level, etc.
    """

    username: str
    uid: str = ""
    display_name: str = ""
    age: str = ""
    country: str = ""
    city: str = ""
    native_langs: list[str] = field(default_factory=list)
    learning_langs: list[str] = field(default_factory=list)
    bio: str = ""                   # full bio text

    def __post_init__(self) -> None:
        if not self.display_name:
            self.display_name = self.username

    @property
    def profile_url(self) -> str:
        return f"https://interpals.net/{self.username}"

    def summary(self) -> str:
        """Plain-text one-liner describing the profile."""
        parts = [self.username]
        if self.age:
            parts.append(f"age {self.age}")
        if self.city and self.country:
            parts.append(f"{self.city}, {self.country}")
        elif self.country:
            parts.append(self.country)
        if self.native_langs:
            parts.append(f"native: {', '.join(self.native_langs)}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return f"<Profile {self.username!r} uid={self.uid!r} country={self.country!r}>"
