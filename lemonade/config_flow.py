"""Config flow for Lemonade Server."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_MODEL, CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LemonadeAuthError, LemonadeClient, LemonadeError
from .const import CONF_TIMEOUT, DEFAULT_MODEL, DEFAULT_NAME, DEFAULT_TIMEOUT, DEFAULT_URL, DOMAIN


DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Optional(CONF_API_KEY): str,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(float),
    }
)


async def _async_validate_connection(
    hass: HomeAssistant,
    url: str,
    api_key: str | None,
    timeout: float,
) -> dict[str, str]:
    """Validate that Lemonade Server is reachable."""
    errors: dict[str, str] = {}
    client = LemonadeClient(async_get_clientsession(hass), url, api_key, timeout)

    try:
        await client.health()
    except LemonadeAuthError:
        errors["base"] = "invalid_auth"
    except (TimeoutError, aiohttp.ClientError):
        errors["base"] = "cannot_connect"
    except LemonadeError:
        errors["base"] = "cannot_connect"
    except Exception:  # noqa: BLE001 - surface unexpected config-flow failures in logs
        errors["base"] = "unknown"

    return errors


class LemonadeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lemonade Server."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        errors: dict[str, str] = {}
        url = user_input[CONF_URL].strip().rstrip("/")
        api_key = user_input.get(CONF_API_KEY)
        if isinstance(api_key, str):
            api_key = api_key.strip() or None
        model = user_input.get(CONF_MODEL, DEFAULT_MODEL).strip()
        timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        try:
            url = cv.url(url)
        except vol.Invalid:
            errors["base"] = "invalid_url"

        if not errors:
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()
            errors = await _async_validate_connection(self.hass, url, api_key, timeout)

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
                errors=errors,
            )

        data: dict[str, Any] = {
            CONF_URL: url,
            CONF_MODEL: model,
            CONF_TIMEOUT: timeout,
        }
        if api_key:
            data[CONF_API_KEY] = api_key

        return self.async_create_entry(
            title=user_input.get(CONF_NAME, DEFAULT_NAME),
            data=data,
        )
