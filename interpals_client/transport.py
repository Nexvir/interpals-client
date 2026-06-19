# interpals_client/transport.py
"""
Thin transport layer on top of aiohttp.

Centralizes error translation so call sites (auth, threads, messages,
search, profiles) don't each need their own try/except around network
calls. Use :func:`request` instead of calling ``session.request`` directly
when you want aiohttp failures translated into interpals-client exceptions.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import aiohttp

from .exceptions import NetworkError, RateLimitError


@asynccontextmanager
async def request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    proxy: Optional[str] = None,
    **kwargs,
) -> AsyncIterator[aiohttp.ClientResponse]:
    """
    Async context manager wrapping ``session.request``.

    Translates:
      - connection/timeout failures → :class:`~interpals_client.exceptions.NetworkError`
      - HTTP 429                    → :class:`~interpals_client.exceptions.RateLimitError`

    Other status codes are returned as-is for the caller to inspect
    (most endpoints here use non-standard status conventions, e.g. 302
    on successful login).
    """
    try:
        async with session.request(method, url, proxy=proxy, **kwargs) as response:
            if response.status == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    f"Rate limited on {method} {url}",
                    retry_after=int(retry_after) if retry_after and retry_after.isdigit() else None,
                )
            yield response
    except RateLimitError:
        raise
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise NetworkError(f"{method} {url} failed: {exc}") from exc
