"""Connection policy for Lemonade Server."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiohttp

from .api import LemonadeAuthError, LemonadeClient, LemonadeError
from .const import DEFAULT_INFERENCE_TIMEOUT, DEFAULT_TIMEOUT


@dataclass(frozen=True)
class ConnectionSettings:
    """Immutable connection settings for a Lemonade Server probe."""

    url: str
    api_key: str | None = None
    timeout: float = DEFAULT_TIMEOUT
    inference_timeout: float = DEFAULT_INFERENCE_TIMEOUT
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        """Normalize values before constructing the client."""
        object.__setattr__(self, "url", self.url.strip().rstrip("/"))
        object.__setattr__(
            self,
            "api_key",
            self.api_key.strip() if self.api_key and self.api_key.strip() else None,
        )


class ConnectionFailureKind(Enum):
    """Classified outcomes from probing a Lemonade Server."""

    AUTH = "auth"
    TRANSPORT = "transport"
    SERVER = "server"
    UNKNOWN = "unknown"


class ConnectionProbeError(Exception):
    """A failed connection probe with a stable failure classification."""

    def __init__(self, kind: ConnectionFailureKind, cause: Exception) -> None:
        """Initialize the classified probe error."""
        super().__init__(str(cause))
        self.kind = kind


async def async_create_verified_client(
    session: Any,
    settings: ConnectionSettings,
) -> LemonadeClient:
    """Build and health-check a Lemonade client, classifying probe failures."""
    client = LemonadeClient(
        session,
        settings.url,
        api_key=settings.api_key,
        timeout=settings.timeout,
        inference_timeout=settings.inference_timeout,
        verify_ssl=settings.verify_ssl,
    )

    try:
        await client.health()
    except LemonadeAuthError as err:
        raise ConnectionProbeError(ConnectionFailureKind.AUTH, err) from err
    except (TimeoutError, aiohttp.ClientError, ConnectionError) as err:
        raise ConnectionProbeError(ConnectionFailureKind.TRANSPORT, err) from err
    except LemonadeError as err:
        raise ConnectionProbeError(ConnectionFailureKind.SERVER, err) from err
    except Exception as err:  # noqa: BLE001 - adapters need a stable unknown outcome
        raise ConnectionProbeError(ConnectionFailureKind.UNKNOWN, err) from err

    return client
