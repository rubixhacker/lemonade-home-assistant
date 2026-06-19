"""The Lemonade Server integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import LemonadeAuthError, LemonadeClient, LemonadeError
from .const import (
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_TIMEOUT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_REPAIR_CAPABILITIES = (CAPABILITY_IMAGE, CAPABILITY_TTS, CAPABILITY_STT)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Lemonade Server."""
    hass.data.setdefault(DOMAIN, {})
    async_register_services(hass)
    return True


def _async_update_missing_capability_issues(
    hass: HomeAssistant,
    entry_id: str,
    coordinator: Any,
) -> None:
    """Create or delete repair issues for missing optional capabilities."""
    from .repairs import (
        async_create_missing_capability_issue,
        async_delete_missing_capability_issue,
    )

    for capability in _REPAIR_CAPABILITIES:
        if coordinator.catalog.model_ids(capability):
            async_delete_missing_capability_issue(hass, entry_id, capability)
        else:
            async_create_missing_capability_issue(hass, entry_id, capability)


def _async_delete_missing_capability_issues(
    hass: HomeAssistant, entry_id: str
) -> None:
    """Delete repair issues for optional capabilities tied to an entry."""
    from .repairs import async_delete_missing_capability_issue

    for capability in _REPAIR_CAPABILITIES:
        async_delete_missing_capability_issue(hass, entry_id, capability)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lemonade Server from a config entry."""
    api_key = entry.options.get(CONF_API_KEY, entry.data.get(CONF_API_KEY))
    timeout = entry.options.get(
        CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    )
    client = LemonadeClient(
        async_get_clientsession(hass),
        entry.data[CONF_URL],
        api_key,
        timeout,
    )

    try:
        async with asyncio.timeout(timeout):
            await client.health()
    except LemonadeAuthError as err:
        raise ConfigEntryAuthFailed from err
    except (TimeoutError, aiohttp.ClientError, ConnectionError) as err:
        raise ConfigEntryNotReady(err) from err
    except LemonadeError as err:
        raise ConfigEntryError(err) from err

    from .coordinator import LemonadeCoordinator
    from .data import LemonadeRuntimeData

    coordinator = LemonadeCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = LemonadeRuntimeData(client=client, coordinator=coordinator)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    _async_update_missing_capability_issues(hass, entry.entry_id, coordinator)
    entry.async_on_unload(
        coordinator.async_add_listener(
            lambda: _async_update_missing_capability_issues(
                hass, entry.entry_id, coordinator
            )
        )
    )

    if PLATFORMS:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Lemonade Server config entry."""
    if PLATFORMS and not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    _async_delete_missing_capability_issues(hass, entry.entry_id)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload Lemonade Server when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)

