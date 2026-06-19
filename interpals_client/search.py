# interpals_client/search.py
"""
User search: build query parameters and parse result pages.
"""
from __future__ import annotations

import re
import html as html_module
from typing import Optional

import aiohttp

from .models.user import User
from . import transport

_BASE = "https://interpals.net"

# ── Path / filename constants that are not usernames ─────────────────────────

_RESERVED: set[str] = {
    "app", "www", "", "images", "css", "js", "static", "img",
    "signup", "login", "search", "online", "messages", "account",
    "forum", "forums", "about", "help", "feedback", "safety",
    "privacy", "tos", "faq", "blog", "donate", "advertise", "jobs",
    "assets", "asset", "fonts", "font", "icons", "icon",
    "site.webmanifest", "manifest.json", "favicon.ico",
    "robots.txt", "sitemap.xml", "sw.js", "service-worker.js",
    "apple-touch-icon.png", "browserconfig.xml",
}

_STATIC_EXT = re.compile(
    r'\.(?:png|jpe?g|gif|svg|ico|webmanifest|json|xml|js|css|txt|woff2?|ttf|map)$',
    re.IGNORECASE,
)


def _valid_username(username: str) -> bool:
    if not username:
        return False
    lower = username.lower()
    return (
        lower not in _RESERVED
        and not lower.startswith("app")
        and not _STATIC_EXT.search(username)
        and "." not in username
    )


# ── Search parameter builder ─────────────────────────────────────────────────

def build_search_params(
    csrf_token: str,
    *,
    sex: Optional[str] = None,          # "male" | "female" | None
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    country: Optional[str] = None,
    native_lang: Optional[str] = None,
    learning_lang: Optional[str] = None,
    keywords: Optional[str] = None,
    online_only: bool = False,
    sort: str = "last_login",
    page: int = 1,
) -> dict:
    """
    Build a ``dict`` of query parameters for GET /app/search.

    All filter arguments are optional.
    """
    offset = (page - 1) * 20
    params: dict = {
        "offset":     str(offset),
        "page":       str(page),
        "viewMode":   "list",
        "sort":       sort,
        "csrf_token": csrf_token,
    }

    if sex and sex.lower() in ("male", "female"):
        params["sex[]"] = sex.lower()
    if age_min is not None:
        params["age1"] = str(age_min)
    if age_max is not None:
        params["age2"] = str(age_max)
    if country:
        params["country"] = country
    if native_lang:
        params["native_lang"] = native_lang
    if learning_lang:
        params["learn_lang"] = learning_lang
    if keywords:
        params["keywords"] = keywords
    if online_only:
        params["online"] = "on"

    return params


# ── HTTP helper ───────────────────────────────────────────────────────────────

async def search_users(
    session: aiohttp.ClientSession,
    proxy: Optional[str],
    csrf_token: str,
    **kwargs,
) -> tuple[list[User], Optional[str]]:
    """
    Fetch one page of search results from /app/search.

    Accepts the same keyword arguments as :func:`build_search_params`.

    Returns ``(users, new_csrf_token)``.
    """
    params = build_search_params(csrf_token, **kwargs)
    async with transport.request(
        session, "GET", f"{_BASE}/app/search",
        params=params,
        proxy=proxy,
        headers={"Referer": f"{_BASE}/app/search"},
    ) as r:
        html = await r.text()

    csrf_m = re.search(r'name="csrf_token"\s+content="([^"]+)"', html)
    new_csrf = csrf_m.group(1) if csrf_m else None

    return parse_search_results(html), new_csrf


# ── HTML parser ───────────────────────────────────────────────────────────────

def parse_search_results(html: str) -> list[User]:
    """
    Parse the HTML from ``/app/search`` and return a list of :class:`User` objects.

    Note: In the 2026 site redesign, ``/app/messages/send?uid=`` links are
    absent from search cards. UIDs must be fetched from full profile pages via
    :func:`~interpals_client.profiles.parse_profile`.
    """
    users: list[User] = []
    seen: set[str] = set()

    link_re = re.compile(
        r'href="(?:https?://(?:www\.)?interpals\.net)?/([a-zA-Z][a-zA-Z0-9_.\-]{1,30})(?:[/"?])'
    )

    for m in link_re.finditer(html):
        username = m.group(1)
        if not _valid_username(username) or username in seen:
            continue
        seen.add(username)

        # uid (present only in older layouts)
        window = html[m.start() : m.end() + 1500]
        uid    = ""
        uid_m  = re.search(r'/app/messages/send\?uid=(\d+)', window)
        if uid_m:
            uid = uid_m.group(1)

        chunk = html[max(0, m.start() - 200) : m.start() + 1500]

        age = ""
        am  = re.search(r'\b(1[6-9]|[2-5]\d)\b', chunk[:800])
        if am:
            age = am.group(1)

        country = city = ""
        loc_m = re.search(r'([A-Z][a-zA-Z\s]+),\s*([A-Z][a-zA-Z\s]+)', chunk[:1000])
        if loc_m:
            city    = loc_m.group(1).strip()
            country = loc_m.group(2).strip()

        native_langs   = re.findall(r'Native[:\s]+([A-Za-z]+)', chunk)
        learning_langs = re.findall(r'(?:Practicing|Learning)[:\s]+([A-Za-z]+)', chunk)

        display_name = username
        dn_m = re.search(r'<[^>]+class="[^"]*font-semibold[^"]*"[^>]*>([^<]{2,40})<', chunk)
        if dn_m:
            display_name = html_module.unescape(dn_m.group(1).strip())

        users.append(
            User(
                username=username,
                uid=uid,
                display_name=display_name,
                age=age,
                country=country,
                city=city,
                native_langs=native_langs,
                learning_langs=learning_langs,
            )
        )

    return users
