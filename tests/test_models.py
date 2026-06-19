# tests/test_models.py
"""Smoke tests — no network required."""
import pytest
from datetime import datetime, timezone

from interpals_client.models.message import Author, Message
from interpals_client.models.thread  import Thread
from interpals_client.models.user    import User
from interpals_client.models.profile import Profile
from interpals_client.search  import parse_search_results, _valid_username
from interpals_client.profiles import parse_profile


# ── model tests ──────────────────────────────────────────────────────────────

def test_message_age():
    now = datetime.now(timezone.utc).isoformat()
    m   = Message(id="1", content="hi", created_at=now, author=Author("alice"))
    assert m.age_seconds < 2


def test_thread_defaults():
    t = Thread(id="42")
    assert t.has_unread is False
    assert t.username is None


def test_user_profile_url():
    u = User(username="bob")
    assert u.profile_url == "https://interpals.net/bob"
    assert u.display_name == "bob"   # auto-filled from username


def test_profile_summary():
    p = Profile(
        username="alice", age="25", country="France", city="Paris",
        native_langs=["French"]
    )
    s = p.summary()
    assert "alice" in s
    assert "Paris" in s
    assert "French" in s


# ── username validation ────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("alice",             True),
    ("bob_99",            True),
    ("app",               False),
    ("",                  False),
    ("favicon.ico",       False),
    ("site.webmanifest",  False),
    ("some.thing",        False),   # dot not allowed
    ("login",             False),
])
def test_valid_username(name, expected):
    assert _valid_username(name) is expected


# ── search parser ─────────────────────────────────────────────────────────────

SEARCH_HTML = """
<html>
<a href="https://interpals.net/alice_w" title="View profile">Alice</a>
<div class="font-semibold">Alice W</div>

<a href="https://interpals.net/bob_z">Bob</a>

<a href="/app/search">not a user</a>
<a href="/login">also not</a>
</html>
"""

def test_parse_search_results_basic():
    users = parse_search_results(SEARCH_HTML)
    names = {u.username for u in users}
    assert "alice_w" in names
    assert "bob_z"   in names
    # reserved paths must be excluded
    assert "app"   not in names
    assert "login" not in names


# ── profile parser ─────────────────────────────────────────────────────────────

PROFILE_HTML = """
<html>
<h1>Alice Wonder</h1>
<span class="truncate">Berlin, Germany</span>
<div class="bg-white/10">27 <i class="fas fa-venus"></i></div>
<span class="text-gray-700">German</span>
<div aria-label="Language level 5 of 4"></div>
<span class="text-gray-700">English</span>
<div aria-label="Language level 3 of 4"></div>
<p>I enjoy hiking and reading books on long weekends in the mountains.</p>
<a href="/app/messages/send?uid=98765">Send message</a>
</html>
"""

def test_parse_profile():
    p = parse_profile(PROFILE_HTML, "alice_w")
    assert p.username     == "alice_w"
    assert p.uid          == "98765"
    assert p.display_name == "Alice Wonder"
    assert p.country      == "Germany"
    assert p.city         == "Berlin"
    assert p.age          == "27"
    assert "German"  in p.native_langs
    assert "English" in p.learning_langs
    assert "hiking"  in p.bio
