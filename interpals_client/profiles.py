# interpals_client/profiles.py
"""
Fetch and parse full user profile pages.
"""
from __future__ import annotations

import re
import html as html_module
from typing import Optional

import aiohttp

from .models.profile import Profile
from .exceptions import ProfileNotFoundError
from . import transport

_BASE = "https://interpals.net"


async def get_profile(
    session: aiohttp.ClientSession,
    username: str,
    proxy: Optional[str],
    referer: str = f"{_BASE}/app/search",
) -> Profile:
    """
    GET ``https://interpals.net/<username>`` and return a :class:`Profile`.

    Raises :class:`~interpals_client.exceptions.ProfileNotFoundError` if the
    profile page returns HTTP 404.
    """
    async with transport.request(
        session, "GET", f"{_BASE}/{username}",
        proxy=proxy,
        headers={"Referer": referer},
    ) as r:
        if r.status == 404:
            raise ProfileNotFoundError(f"No profile found for username={username!r}")
        html = await r.text()

    return parse_profile(html, username)


def parse_profile(html: str, username: str) -> Profile:
    """
    Parse a full profile page HTML and return a :class:`Profile`.

    Regex patterns are derived from the 2026 site layout:
      - uid        : ``/app/messages/send?uid=XXXX``
      - city/country : ``<span class="truncate">City, Country</span>``
      - languages  : ``aria-label="Language level X of 4"`` (≥5 = Native)
      - bio        : common English bio-opening phrases
    """

    # ── uid ──────────────────────────────────────────────────────
    uid = ""
    for pat in [
        r'/app/messages/send\?uid=(\d+)',
        r'data-uid="(\d+)"',
        r'"uid"\s*:\s*"(\d+)"',
    ]:
        m = re.search(pat, html)
        if m:
            uid = m.group(1)
            break

    # ── display name ─────────────────────────────────────────────
    display_name = username
    m = re.search(r'<h1[^>]*>\s*([^<]{2,60})\s*</h1>', html)
    if m:
        candidate = html_module.unescape(m.group(1)).strip()
        if candidate and "interpals" not in candidate.lower() and len(candidate) < 50:
            display_name = candidate

    # ── city / country ───────────────────────────────────────────
    city = country = ""
    m = re.search(r'<span class="truncate">([^<,]+),\s*([^<]+)</span>', html)
    if m:
        city    = html_module.unescape(m.group(1)).strip()
        country = html_module.unescape(m.group(2)).strip()
    if not country:
        m = re.search(r'<span class="truncate">([A-Z][^<,]{3,30})</span>', html)
        if m:
            country = html_module.unescape(m.group(1)).strip()

    # ── age ──────────────────────────────────────────────────────
    age = ""
    for pat in [
        r'bg-white/10[^>]*>\s*(\d{2})\s*(?:<i|<span)',
        r'border-r[^>]*>\s*(\d{2})\s*(?:<i|<span)',
        r'\b(1[6-9]|[2-6]\d)\s*years?\s*old\b',
        r'"age"\s*:\s*(\d{2})',
    ]:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 16 <= val <= 70:
                    age = str(val)
                    break
            except ValueError:
                pass

    # ── bio ──────────────────────────────────────────────────────
    bio = ""
    bio_starters = (
        r'((?:looking\s+to|I\s+enjoy|I\s+hope|I\s+like|I\s+love|I\'m\s+looking|'
        r'I\s+am\s+looking|Hi,?\s+I\'m|Hello[,!]?\s+I\'m|Hey[,!]?\s+I\'m|'
        r'My\s+name\s+is|I\s+am\s+a)[^<]{20,600})'
    )
    m = re.search(bio_starters, html, re.IGNORECASE | re.DOTALL)
    if m:
        raw     = re.sub(r'<[^>]+>', ' ', m.group(1))
        cleaned = html_module.unescape(re.sub(r'\s+', ' ', raw)).strip()
        if len(cleaned) > 30:
            bio = cleaned[:500]

    if not bio:
        # Fallback: largest clean paragraph
        blocks = re.findall(
            r'<(?:p|div)[^>]{0,80}>\s*([A-Za-z][^<]{40,600})\s*</(?:p|div)>', html
        )
        _skip = {"won't be able", "interpals", "cookie", "Privacy", "©",
                 "bookmark", "block", "report", "message request"}
        candidates = [
            html_module.unescape(re.sub(r'\s+', ' ', b)).strip()
            for b in blocks
            if not any(s in b for s in _skip) and len(b.split()) >= 6
        ]
        if candidates:
            bio = max(candidates, key=len)[:500]

    bio = re.sub(r'\s+', ' ', bio).strip()

    # ── languages ────────────────────────────────────────────────
    native_langs: list[str]   = []
    learning_langs: list[str] = []

    for lang, level in re.findall(
        r'<span[^>]*text-gray-700[^>]*>\s*([A-Za-z]+)\s*</span>\s*'
        r'<div[^>]*aria-label="Language level (\d+) of \d+"',
        html,
    ):
        (native_langs if int(level) >= 5 else learning_langs).append(lang)

    # JSON fallback
    if not native_langs:
        jm = re.search(r'"native_lang"\s*:\s*"([^"]+)"', html)
        if jm:
            native_langs = [jm.group(1)]
    if not learning_langs:
        jm = re.search(r'"learning_lang"\s*:\s*"([^"]+)"', html)
        if jm:
            learning_langs = [jm.group(1)]

    return Profile(
        username=username,
        uid=uid,
        display_name=display_name,
        age=age,
        country=country,
        city=city,
        native_langs=native_langs,
        learning_langs=learning_langs,
        bio=bio,
    )
