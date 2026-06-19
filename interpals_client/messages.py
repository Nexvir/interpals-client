# interpals_client/messages.py
"""
Low-level functions for reading and sending messages.

All functions accept a live :class:`aiohttp.ClientSession` and the current
``csrf_token`` string — session/auth management is handled by the caller
(:class:`~interpals_client.client.InterpalsClient`).
"""
from __future__ import annotations

import re
import html as html_module
from datetime import datetime, timezone
from typing import Optional

import aiohttp

from .models.message import Author, Message
from .exceptions import SendMessageError, ThreadNotFoundError
from . import transport

_BASE = "https://interpals.net"


async def load_messages(
    session: aiohttp.ClientSession,
    thread_id: str,
    csrf_token: str,
    proxy: Optional[str],
    limit: int = 10,
) -> list[Message]:
    """
    POST /app/messages/load and return up to *limit* :class:`Message` objects,
    newest first.

    Raises :class:`~interpals_client.exceptions.ThreadNotFoundError` if the
    thread does not exist or is not accessible.
    """
    form = {
        "thread":     str(thread_id),
        "load_draft": "1",
        "csrf_token": csrf_token,
    }
    async with transport.request(
        session, "POST", f"{_BASE}/app/messages/load",
        data=form,
        proxy=proxy,
        headers={
            "Content-Type":     "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer":          f"{_BASE}/app/messages",
            "Origin":           _BASE,
            "X-Requested-With": "XMLHttpRequest",
            "Accept":           "application/json, text/javascript, */*; q=0.01",
        },
    ) as r:
        if r.status == 404:
            raise ThreadNotFoundError(f"No thread found for thread_id={thread_id!r}")
        data = await r.json(content_type=None)

    body = data.get("body", "")
    msgs = _parse_messages_html(body)
    msgs.reverse()          # newest first
    return msgs[:limit]


async def send_message(
    session: aiohttp.ClientSession,
    thread_id: str,
    content: str,
    csrf_token: str,
    proxy: Optional[str],
) -> dict:
    """
    POST /app/messages/send-message.

    Confirmed endpoint from HAR analysis. Returns the raw JSON response.
    Raises :class:`~interpals_client.exceptions.SendMessageError` on failure.
    """
    await _send_typing(session, thread_id, proxy)

    form = {
        "thread":     str(thread_id),
        "message":    content,
        "csrf_token": csrf_token,
    }
    async with transport.request(
        session, "POST", f"{_BASE}/app/messages/send-message",
        data=form,
        proxy=proxy,
        headers={
            "Content-Type":     "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer":          f"{_BASE}/app/messages?thread_id={thread_id}",
            "Origin":           _BASE,
            "X-Requested-With": "XMLHttpRequest",
            "Accept":           "application/json, text/javascript, */*; q=0.01",
        },
    ) as r:
        status = r.status
        try:
            resp = await r.json(content_type=None)
        except Exception:
            resp = await r.text()

    if status != 200:
        raise SendMessageError(
            f"HTTP {status} — body={str(resp)[:200]}"
        )
    if isinstance(resp, dict) and "body" not in resp:
        raise SendMessageError(f"Unexpected response: {str(resp)[:200]}")

    return resp if isinstance(resp, dict) else {}


async def _send_typing(
    session: aiohttp.ClientSession,
    thread_id: str,
    proxy: Optional[str],
) -> None:
    """PUT /v1/thread/{id}/typing — best-effort, never raises."""
    try:
        async with session.put(
            f"{_BASE}/v1/thread/{thread_id}/typing",
            data="delay=3000",
            proxy=proxy,
            headers={
                "Content-Type":     "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            },
        ):
            pass
    except Exception:
        pass


# ── HTML parser ──────────────────────────────────────────────────────────────

def _parse_messages_html(body: str) -> list[Message]:
    """Parse the ``body`` HTML fragment from the messages/load response."""
    messages: list[Message] = []

    date_positions = [
        (m.start(), m.group(1))
        for m in re.finditer(r'data-date="(\d{8})"', body)
    ]

    msg_re = re.compile(
        r'<div class="pm_msg\s*([^"]*)"\s*'
        r'id="msg_(\d+)"\s*'
        r'data-sender-id="(\d+)"\s*'
        r'data-sender-name="([^"]*)"'
    )

    for m in msg_re.finditer(body):
        classes     = m.group(1)
        msg_id      = m.group(2)
        sender_id   = m.group(3)
        sender_name = html_module.unescape(m.group(4))
        is_own      = "own_msg" in classes

        # Find the most recent date-div before this message
        current_date: Optional[str] = None
        for pos, d in date_positions:
            if pos < m.start():
                current_date = d
            else:
                break

        chunk = body[m.end() : m.end() + 2000]

        bm = re.search(r'msg_body[^"]*"[^>]*>\s*(.*?)\s*<', chunk, re.DOTALL)
        content = html_module.unescape(bm.group(1).strip()) if bm else ""

        tm = re.search(r'<span class="text-zinc-500 text-xs mr-1">([^<]*)</span>', chunk)
        time_str = tm.group(1).strip() if tm else "00:00"

        created_at = _build_timestamp(current_date, time_str)
        messages.append(
            Message(
                id=msg_id,
                content=content,
                created_at=created_at,
                author=Author(name=sender_name, id=sender_id),
                is_own=is_own,
            )
        )

    return messages


def _build_timestamp(date_str: Optional[str], time_str: str) -> str:
    """Convert ``'YYYYMMDD'`` + ``'HH:MM'`` → ISO 8601 (UTC approximate)."""
    try:
        if date_str:
            y, mo, d = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
        else:
            now = datetime.now(timezone.utc)
            y, mo, d = now.year, now.month, now.day

        parts = time_str.split(":")
        hh, mm = (int(parts[0]), int(parts[1])) if len(parts) >= 2 else (0, 0)
        return datetime(y, mo, d, hh, mm, tzinfo=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()
