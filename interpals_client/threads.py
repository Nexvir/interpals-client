# interpals_client/threads.py
"""
Functions for reading the inbox thread list.
"""
from __future__ import annotations

import re
import html as html_module
from typing import Optional

import aiohttp

from .models.thread import Thread
from . import transport

_BASE = "https://interpals.net"


async def get_threads(
    session: aiohttp.ClientSession,
    proxy: Optional[str],
) -> tuple[list[Thread], Optional[str]]:
    """
    GET /app/messages and parse all ``pm_thread`` blocks.

    Returns ``(threads, new_csrf_token)``.
    The caller is responsible for storing the updated csrf token.
    """
    async with transport.request(session, "GET", f"{_BASE}/app/messages", proxy=proxy) as r:
        html = await r.text()

    csrf_m = re.search(r'name="csrf_token"\s+content="([^"]+)"', html)
    csrf   = csrf_m.group(1) if csrf_m else None

    threads = _parse_threads(html)
    return threads, csrf


def _parse_threads(html: str) -> list[Thread]:
    threads: list[Thread] = []
    seen: set[str] = set()

    for m in re.finditer(
        r'data-thread-id="(\d+)"\s+id="thread_\d+"\s+class="pm_thread([^"]*)"',
        html,
    ):
        thread_id   = m.group(1)
        css_classes = m.group(2)
        if thread_id in seen:
            continue
        seen.add(thread_id)

        chunk = html[m.end() : m.end() + 3000]

        # username
        username = None
        um = re.search(
            r'href="https://(?:www\.)?interpals\.net/([^"\?#]+)[^"]*"\s+title="View',
            chunk,
        )
        if not um:
            um = re.search(
                r'<a href="https://(?:www\.)?interpals\.net/([^"\?#/]+)', chunk
            )
        if um and um.group(1) not in ("app", ""):
            username = um.group(1)

        # display name
        dm = re.search(r'font-medium text-gray-900[^"]*">([^<]+)<', chunk)
        display_name = dm.group(1).strip() if dm else None

        # snippet (last message preview)
        sm = re.search(r'th_snippet[^"]*"[^>]*>(.*?)</a>', chunk, re.DOTALL)
        snippet = None
        if sm:
            inner = sm.group(1)
            tm = re.search(
                r'<span class="truncate">\s*(.*?)\s*</span>', inner, re.DOTALL
            )
            if tm:
                snippet = html_module.unescape(tm.group(1).strip())

        # unread: scan the full thread block for any unread indicator
        next_m    = re.search(r'data-thread-id="', html[m.end():])
        block_end = m.end() + (next_m.start() if next_m else 6000)
        block     = html[m.start() : block_end]
        has_unread = (
            "pm_unread" in css_classes
            or bool(re.search(r"pm_unread", block))
            or bool(re.search(r'data-unread="[^0]', block))
            or bool(re.search(r'<span[^>]+class="[^"]*badge[^"]*"[^>]*>[1-9]', block))
            or bool(re.search(r'class="[^"]*unread[^"]*"', block))
        )

        threads.append(
            Thread(
                id=thread_id,
                username=username,
                display_name=display_name,
                snippet=snippet,
                has_unread=has_unread,
                inactive="inactive" in css_classes,
            )
        )

    return threads
