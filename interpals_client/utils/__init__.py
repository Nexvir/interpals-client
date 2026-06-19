# interpals_client/utils/__init__.py
"""Small helper utilities for interpals-client."""

from __future__ import annotations

import logging


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the ``interpals_client`` logger.

    Attaches a simple stream handler if one isn't already present, so
    repeated calls (e.g. in notebooks) don't duplicate log lines.

    Parameters
    ----------
    level :
        Logging level, e.g. ``logging.DEBUG`` for verbose HTTP/parse traces.

    Returns
    -------
    logging.Logger
        The configured ``"interpals_client"`` logger instance.
    """
    logger = logging.getLogger("interpals_client")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)

    return logger


__all__ = ["setup_logging"]
