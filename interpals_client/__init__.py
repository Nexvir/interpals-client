# interpals_client/__init__.py
"""
interpals-client
================
Async Python client for the interpals.net private-messaging API.

Quick start::

    import asyncio
    from interpals_client import InterpalsClient

    async def main():
        async with InterpalsClient("alice", "s3cr3t") as client:
            await client.login()

            # inbox
            threads = await client.get_threads()

            # read messages
            msgs = await client.get_messages(threads[0].id)
            for m in msgs:
                print(m.author.name, ":", m.content)

            # send a reply
            await client.send_message(threads[0].id, "Hey!")

            # search users
            users = await client.search(country="Germany", age_min=20, age_max=30)

            # full profile
            profile = await client.get_profile(users[0].username)
            print(profile.bio)

    asyncio.run(main())
"""

__version__ = "0.1.0"
__all__ = [
    # Main client
    "InterpalsClient",
    # Models
    "Message",
    "Thread",
    "User",
    "Profile",
    "Author",
    # Exceptions
    "InterpalsError",
    "AuthError",
    "NotLoggedInError",
    "CSRFError",
    "NetworkError",
    "RateLimitError",
    "SendMessageError",
    "ThreadNotFoundError",
    "UserNotFoundError",
    "ProfileNotFoundError",
    "ParseError",
    # Lower-level helpers (for power users / extensions)
    "parse_search_results",
    "parse_profile",
    "build_search_params",
    # Logging
    "setup_logging",
]

from .client     import InterpalsClient
from .models     import Author, Message, Thread, User, Profile
from .exceptions import (
    InterpalsError,
    AuthError,
    NotLoggedInError,
    CSRFError,
    NetworkError,
    RateLimitError,
    SendMessageError,
    ThreadNotFoundError,
    UserNotFoundError,
    ProfileNotFoundError,
    ParseError,
)
from .search     import parse_search_results, build_search_params
from .profiles   import parse_profile
from .utils      import setup_logging
