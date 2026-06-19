# interpals-client

Async Python client for the **interpals.net** private-messaging API.

> **This is a pure HTTP client SDK.**  
> AI bots, outreach engines, and dashboards live in a separate package: [`interpals-bot`](https://github.com/your-org/interpals-bot).

---

## Installation

```bash
pip install interpals-client
```

**Requirements:** Python ≥ 3.11, `aiohttp`

---

## Quick Start

```python
import asyncio
from interpals_client import InterpalsClient

async def main():
    async with InterpalsClient("alice", "s3cr3t") as client:
        await client.login()

        # inbox
        threads = await client.get_threads()
        for t in threads:
            print(t.username, "unread:", t.has_unread)

        # read messages
        msgs = await client.get_messages(threads[0].id, limit=5)
        for m in msgs:
            print(f"[{m.author.name}] {m.content}")

        # send a reply
        await client.send_message(threads[0].id, "Hey!")

        # search users
        users = await client.search(country="Germany", age_min=20, age_max=30)

        # full profile
        profile = await client.get_profile(users[0].username)
        print(profile.bio)

asyncio.run(main())
```

---

## API Reference

### `InterpalsClient(username, password, proxy=None)`

The main client.  All methods are `async`.

| Method | Description |
|---|---|
| `await login()` | Authenticate. Must be called first. |
| `await get_threads()` | List inbox threads → `list[Thread]` |
| `await get_messages(thread_id, limit=10)` | Read messages → `list[Message]` (newest first) |
| `await send_message(thread_id, content)` | Send a message |
| `await search(**filters)` | Search users → `list[User]` |
| `await get_profile(username)` | Full profile page → `Profile` |
| `await close()` | Close the HTTP session |

#### `search()` keyword arguments

| Argument | Type | Description |
|---|---|---|
| `sex` | `str` | `"male"` or `"female"` |
| `age_min` / `age_max` | `int` | Age range |
| `country` | `str` | Country name |
| `native_lang` | `str` | Native language |
| `learning_lang` | `str` | Language being learnt |
| `keywords` | `str` | Bio keyword search |
| `online_only` | `bool` | Only online users |
| `sort` | `str` | Sort order (default `"last_login"`) |
| `page` | `int` | Result page (20 per page) |

---

### Models

| Class | Key fields |
|---|---|
| `Thread` | `id`, `username`, `display_name`, `snippet`, `has_unread` |
| `Message` | `id`, `content`, `created_at`, `author`, `is_own`, `.age_seconds` |
| `Author` | `name`, `id` |
| `User` | `username`, `uid`, `age`, `country`, `city`, `native_langs`, `learning_langs` |
| `Profile` | All `User` fields + `bio`, `.summary()`, `.profile_url` |

---

### Exceptions

| Exception | When raised |
|---|---|
| `InterpalsError` | Base class |
| `AuthError` | Wrong credentials |
| `NotLoggedInError` | API called before `login()` |
| `SendMessageError` | Message delivery failed |
| `ThreadNotFoundError` | `thread_id` does not exist or isn't accessible |
| `UserNotFoundError` | Username does not exist |
| `ProfileNotFoundError` | Profile page returned 404 (subclass of `UserNotFoundError`) |
| `CSRFError` | Could not obtain/refresh a CSRF token (subclass of `AuthError`) |
| `NetworkError` | Connection/timeout failure talking to interpals.net |
| `RateLimitError` | Server returned HTTP 429; `.retry_after` has the suggested wait in seconds |
| `ParseError` | Unexpected HTML structure |

---

## Examples

Runnable scripts in [`examples/`](examples/):

| File | What it shows |
|---|---|
| `examples/login.py` | Minimal login flow |
| `examples/search.py` | Searching users with filters |
| `examples/profile.py` | Fetching a single full profile |
| `examples/messages.py` | Reading inbox + replying to a thread |

Each reads credentials from `INTERPALS_USERNAME` / `INTERPALS_PASSWORD` env vars:

```bash
export INTERPALS_USERNAME=alice
export INTERPALS_PASSWORD=s3cr3t
python examples/search.py
```

---

### Lower-level helpers

For power users or when building `interpals-bot`:

```python
from interpals_client import parse_search_results, parse_profile, build_search_params
```

---

## Package Structure

```
interpals_client/
├── __init__.py       ← public API
├── client.py         ← InterpalsClient
├── session.py        ← aiohttp session lifecycle (SessionManager)
├── transport.py       ← request wrapper: NetworkError / RateLimitError translation
├── auth.py           ← login, CSRF management
├── threads.py        ← inbox thread listing
├── messages.py       ← load / send messages
├── search.py         ← user search + HTML parser
├── profiles.py       ← full profile fetch + parser
├── exceptions.py     ← exception hierarchy
├── models/
│   ├── message.py    ← Author, Message
│   ├── thread.py     ← Thread
│   ├── user.py       ← User
│   └── profile.py    ← Profile
└── utils/
    └── __init__.py   ← setup_logging()

examples/             ← runnable usage scripts
tests/                ← pytest suite
```

---

## What this SDK does NOT include

Everything bot-related belongs in `interpals-bot` (separate package):

- AI reply generation
- Outreach / first-message automation
- Message queue / database persistence
- Web dashboard
- Rate limiting / quiet hours
- Blacklist management

---

## License

MIT
