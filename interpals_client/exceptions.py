# interpals_client/exceptions.py
"""
Exception hierarchy for interpals-client.

All exceptions inherit from :class:`InterpalsError`, so callers who don't
care about the specific failure mode can catch just that one class.
"""


class InterpalsError(Exception):
    """Base exception for all interpals-client errors."""


class AuthError(InterpalsError):
    """Login failed (bad credentials) or the session expired."""


class NotLoggedInError(InterpalsError):
    """An API method was called before login()."""


class CSRFError(AuthError):
    """A CSRF token could not be obtained or was rejected by the server."""


class NetworkError(InterpalsError):
    """A transport-level failure occurred (timeout, connection reset, DNS, etc.).

    Wraps the underlying ``aiohttp`` exception; see ``__cause__`` for details.
    """


class RateLimitError(InterpalsError):
    """The server responded with HTTP 429 (too many requests).

    ``retry_after`` is the number of seconds suggested by the server's
    ``Retry-After`` header, if present.
    """

    def __init__(self, message: str, retry_after: "int | None" = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class SendMessageError(InterpalsError):
    """Message could not be delivered."""


class ThreadNotFoundError(InterpalsError):
    """The requested thread_id does not exist or is not accessible."""


class UserNotFoundError(InterpalsError):
    """The requested username does not exist."""


class ProfileNotFoundError(UserNotFoundError):
    """A profile page could not be fetched or parsed for a given username."""


class ParseError(InterpalsError):
    """HTML parsing produced an unexpected result."""
