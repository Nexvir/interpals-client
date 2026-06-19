# interpals_client/session.py
"""
Session lifecycle management.

Wraps the creation/teardown of the underlying :class:`aiohttp.ClientSession`,
keeping cookie-jar and header setup in one place.
"""
from __future__ import annotations

from typing import Optional

import aiohttp

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def create_session() -> aiohttp.ClientSession:
    """Build a new :class:`aiohttp.ClientSession` with the standard cookie jar
    and headers used by interpals-client."""
    return aiohttp.ClientSession(
        cookie_jar=aiohttp.CookieJar(unsafe=True),
        headers={"User-Agent": _USER_AGENT},
    )


class SessionManager:
    """
    Owns a single lazily-created :class:`aiohttp.ClientSession` and its
    lifecycle. Used internally by :class:`~interpals_client.client.InterpalsClient`.
    """

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    def get(self) -> aiohttp.ClientSession:
        """Return the live session, creating one if needed or if the previous
        one was closed."""
        if self._session is None or self._session.closed:
            self._session = create_session()
        return self._session

    async def close(self) -> None:
        """Close the session if it's open."""
        if self._session and not self._session.closed:
            await self._session.close()

    @property
    def is_open(self) -> bool:
        return self._session is not None and not self._session.closed
