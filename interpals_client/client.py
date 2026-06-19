# interpals_client/client.py
"""
The primary entry point for interpals-client.

All API operations go through :class:`InterpalsClient`.
"""
from __future__ import annotations

from typing import Optional

import aiohttp

from . import auth as _auth
from . import messages as _messages
from . import threads as _threads
from . import search as _search
from . import profiles as _profiles
from .exceptions import NotLoggedInError
from .session import SessionManager
from .models.message import Message
from .models.thread  import Thread
from .models.user    import User
from .models.profile import Profile


class InterpalsClient:
    """
    Async HTTP client for interpals.net.

    All network I/O is non-blocking (``aiohttp``).  The client manages
    cookies, CSRF tokens, and session lifecycle automatically.

    Usage::

        async with InterpalsClient("alice", "s3cr3t") as client:
            await client.login()

            threads = await client.get_threads()
            msgs    = await client.get_messages(threads[0].id)

            await client.send_message(threads[0].id, "Hey!")

            users   = await client.search(country="Germany", age_min=20, age_max=30)
            profile = await client.get_profile(users[0].username)

    Parameters
    ----------
    username :
        Your interpals.net username.
    password :
        Your interpals.net password.
    proxy :
        Optional HTTP proxy URL (e.g. ``"http://127.0.0.1:10809"``).
    """

    def __init__(
        self,
        username: str,
        password: str,
        proxy: Optional[str] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.proxy    = proxy

        self._sessions: SessionManager = SessionManager()
        self._csrf:    Optional[str] = None
        self._logged_in: bool = False

    # ── Context-manager support ───────────────────────────────────────────────

    async def __aenter__(self) -> "InterpalsClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ── Session ───────────────────────────────────────────────────────────────

    async def _session_(self) -> aiohttp.ClientSession:
        """Return (or create) the underlying aiohttp session."""
        return self._sessions.get()

    async def close(self) -> None:
        """Close the underlying aiohttp session and mark as logged out."""
        await self._sessions.close()
        self._logged_in = False

    def _require_login(self) -> None:
        if not self._logged_in:
            raise NotLoggedInError("Call await client.login() first.")

    async def _refresh_csrf(self) -> None:
        """Fetch /app/messages to get a fresh CSRF token."""
        s = await self._session_()
        _, csrf = await _auth.refresh_csrf_from_messages(s, self.proxy)
        if csrf:
            self._csrf = csrf

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def login(self) -> None:
        """
        Log in to interpals.net.

        Raises :class:`~interpals_client.exceptions.AuthError` on failure.
        """
        s    = await self._session_()
        csrf = await _auth.fetch_csrf(s, self.proxy)
        await _auth.login(s, self.username, self.password, csrf, self.proxy)
        self._logged_in = True
        await self._refresh_csrf()

    # ── Threads ───────────────────────────────────────────────────────────────

    async def get_threads(self) -> list[Thread]:
        """
        Return all conversation threads from the inbox.

        Each :class:`~interpals_client.models.thread.Thread` includes
        ``id``, ``username``, ``display_name``, ``snippet``, and ``has_unread``.
        """
        self._require_login()
        s = await self._session_()
        thread_list, new_csrf = await _threads.get_threads(s, self.proxy)
        if new_csrf:
            self._csrf = new_csrf
        return thread_list

    # ── Messages ──────────────────────────────────────────────────────────────

    async def get_messages(self, thread_id: str, limit: int = 10) -> list[Message]:
        """
        Return up to *limit* messages for *thread_id*, newest first.

        Each :class:`~interpals_client.models.message.Message` includes
        ``id``, ``content``, ``created_at``, ``author``, and ``is_own``.
        """
        self._require_login()
        s = await self._session_()
        return await _messages.load_messages(
            s, thread_id, self._csrf or "", self.proxy, limit=limit
        )

    async def send_message(self, thread_id: str, content: str) -> None:
        """
        Send *content* to an existing *thread_id*.

        Automatically refreshes the CSRF token before sending.

        Raises :class:`~interpals_client.exceptions.SendMessageError` on failure.
        """
        self._require_login()
        await self._refresh_csrf()
        s = await self._session_()
        await _messages.send_message(s, thread_id, content, self._csrf or "", self.proxy)

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(
        self,
        *,
        sex: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        country: Optional[str] = None,
        native_lang: Optional[str] = None,
        learning_lang: Optional[str] = None,
        keywords: Optional[str] = None,
        online_only: bool = False,
        sort: str = "last_login",
        page: int = 1,
    ) -> list[User]:
        """
        Search for users with optional filters.

        Parameters
        ----------
        sex :
            ``"male"`` or ``"female"`` (or omit for any).
        age_min / age_max :
            Age range filter.
        country :
            Country name as interpals accepts it (e.g. ``"Germany"``).
        native_lang :
            Native language filter (e.g. ``"German"``).
        learning_lang :
            Language the user is learning.
        keywords :
            Keywords to search in bios.
        online_only :
            If ``True``, only return currently online users.
        sort :
            Sort order (default ``"last_login"``).
        page :
            Result page number (20 users per page).

        Returns
        -------
        list[User]
        """
        self._require_login()
        s = await self._session_()
        users, new_csrf = await _search.search_users(
            s, self.proxy, self._csrf or "",
            sex=sex, age_min=age_min, age_max=age_max,
            country=country, native_lang=native_lang,
            learning_lang=learning_lang, keywords=keywords,
            online_only=online_only, sort=sort, page=page,
        )
        if new_csrf:
            self._csrf = new_csrf
        return users

    # ── Profiles ─────────────────────────────────────────────────────────────

    async def get_profile(self, username: str) -> Profile:
        """
        Fetch and parse the full profile page for *username*.

        Returns a :class:`~interpals_client.models.profile.Profile` with
        ``uid``, ``bio``, ``native_langs``, ``learning_langs``, etc.
        """
        self._require_login()
        s = await self._session_()
        return await _profiles.get_profile(s, username, self.proxy)
