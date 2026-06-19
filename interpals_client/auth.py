# interpals_client/auth.py
"""
Login and CSRF-token management.

This module is used internally by :class:`~interpals_client.client.InterpalsClient`
and is not typically imported directly by callers.
"""
from __future__ import annotations

import re
from typing import Optional

import aiohttp

from .exceptions import AuthError, CSRFError
from . import transport

_BASE = "https://interpals.net"


async def fetch_csrf(session: aiohttp.ClientSession, proxy: Optional[str]) -> Optional[str]:
    """GET / and extract the csrf_token meta tag value."""
    async with transport.request(session, "GET", _BASE, proxy=proxy) as r:
        html = await r.text()
    return _extract_csrf(html)


async def login(
    session: aiohttp.ClientSession,
    username: str,
    password: str,
    csrf_token: Optional[str],
    proxy: Optional[str],
) -> None:
    """
    POST /app/auth/login with form credentials.

    Raises :class:`~interpals_client.exceptions.CSRFError` if no CSRF token
    was available, or :class:`~interpals_client.exceptions.AuthError` on
    failed login.
    """
    if not csrf_token:
        raise CSRFError("Could not obtain a CSRF token before login.")

    form: dict = {"username": username, "password": password, "csrf_token": csrf_token}

    async with transport.request(
        session, "POST", f"{_BASE}/app/auth/login",
        data=form,
        proxy=proxy,
        allow_redirects=False,
        headers={
            "Content-Type":     "application/x-www-form-urlencoded",
            "Referer":          f"{_BASE}/",
            "Origin":           _BASE,
            "X-Requested-With": "XMLHttpRequest",
        },
    ) as r:
        status   = r.status
        location = r.headers.get("Location", "")

    if status in (302, 303) and "login" not in location.lower():
        return  # success

    raise AuthError(
        f"Login failed — HTTP {status}, Location={location!r}. "
        "Check username / password."
    )


async def refresh_csrf_from_messages(
    session: aiohttp.ClientSession, proxy: Optional[str]
) -> tuple[str, Optional[str]]:
    """
    GET /app/messages and return (html, csrf_token).

    Used to refresh the CSRF token before write operations.
    """
    async with transport.request(session, "GET", f"{_BASE}/app/messages", proxy=proxy) as r:
        html = await r.text()
    return html, _extract_csrf(html)


def _extract_csrf(html: str) -> Optional[str]:
    m = re.search(r'name="csrf_token"\s+content="([^"]+)"', html)
    return m.group(1) if m else None
