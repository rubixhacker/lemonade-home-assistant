"""Shared Lemonade error classification helpers."""

from __future__ import annotations

import aiohttp

from homeassistant.exceptions import HomeAssistantError

from .api import LemonadeError

TIMEOUT_MESSAGE = "Timeout communicating with Lemonade Server"
LEMONADE_CLIENT_EXCEPTIONS = (LemonadeError, aiohttp.ClientError, TimeoutError)


def lemonade_home_assistant_error(
    err: Exception,
    action: str,
    *,
    timeout_message: str | None = TIMEOUT_MESSAGE,
) -> HomeAssistantError:
    """Return a Home Assistant error for a Lemonade client failure."""
    if timeout_message is not None and isinstance(err, TimeoutError):
        return HomeAssistantError(timeout_message)
    return HomeAssistantError(f"{action}: {err}")
