"""Config flow for Lemonade Server."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_MODEL, CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, llm, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.const import CONF_PROMPT
except ImportError:  # pragma: no cover - older Home Assistant compatibility
    CONF_PROMPT = "prompt"

from .api import LemonadeAuthError, LemonadeClient, LemonadeError
from .const import (
    CONF_KEEP_ALIVE,
    CONF_MAX_HISTORY,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    DEFAULT_URL,
    DOMAIN,
    SUBENTRY_TYPE_CONVERSATION,
    default_model_selector_definitions,
)
from .model_resolution import runtime_model_view
from .profiles import (
    ProfileDefinition,
    profile_definition,
    profile_definitions,
)

_LOGGER = logging.getLogger(__name__)


def _entry_current_value(
    config_entry: config_entries.ConfigEntry, key: str, default: Any = None
) -> Any:
    """Return an option value falling back to config entry data."""
    if key in config_entry.options:
        return config_entry.options[key]
    return config_entry.data.get(key, default)


def _model_select_selector(model_ids: list[str]) -> selector.SelectSelector:
    """Return a selector for Lemonade model IDs."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=model_ids,
        )
    )


def _llm_api_options(hass: HomeAssistant) -> list[Any]:
    """Return selector options for Home Assistant LLM APIs."""
    options: list[Any] = []
    for api in llm.async_get_apis(hass):
        if isinstance(api, dict):
            options.append(api)
            continue

        api_id = getattr(api, "id", None)
        if api_id is None:
            continue
        options.append({"value": api_id, "label": getattr(api, "name", api_id)})
    return options


def _number_box_selector(
    *,
    minimum: int,
) -> selector.NumberSelector:
    """Return a number box selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _default_instructions_prompt() -> str | None:
    """Return Home Assistant's default LLM instructions prompt, if available."""
    prompt = getattr(llm, "DEFAULT_INSTRUCTIONS_PROMPT", None)
    return prompt if isinstance(prompt, str) and prompt else None


def _profile_model_ids(
    config_entry: config_entries.ConfigEntry,
    definition: ProfileDefinition,
) -> list[str]:
    """Return selectable model IDs for a profile definition."""
    model_view = runtime_model_view(config_entry)
    if definition.model_policy.include_all_models:
        return model_view.all_model_ids
    return model_view.model_ids(definition.model_policy.capability)


DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Optional(CONF_API_KEY): str,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(float),
        vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
    }
)


async def _async_validate_connection(
    hass: HomeAssistant,
    url: str,
    api_key: str | None,
    timeout: float,
    verify_ssl: bool,
) -> dict[str, str]:
    """Validate that Lemonade Server is reachable."""
    errors: dict[str, str] = {}
    client = LemonadeClient(
        async_get_clientsession(hass),
        url,
        api_key=api_key,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )

    try:
        await client.health()
    except LemonadeAuthError:
        errors["base"] = "invalid_auth"
    except (TimeoutError, aiohttp.ClientError) as err:
        _LOGGER.warning("Failed to connect to Lemonade Server at %s: %s", url, err)
        errors["base"] = "cannot_connect"
    except LemonadeError as err:
        _LOGGER.warning("Lemonade Server validation failed at %s: %s", url, err)
        errors["base"] = "cannot_connect"
    except Exception:  # noqa: BLE001 - surface unexpected config-flow failures in logs
        _LOGGER.exception("Unexpected Lemonade Server validation failure for %s", url)
        errors["base"] = "unknown"

    return errors


class LemonadeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lemonade Server."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LemonadeOptionsFlow:
        """Create the options flow."""
        return LemonadeOptionsFlow(config_entry)

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: config_entries.ConfigEntry
    ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
        """Return supported subentry types."""
        return {
            definition.profile_type: LemonadeProfileSubentryFlow
            for definition in profile_definitions()
        }

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
        timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        verify_ssl = user_input.get(CONF_VERIFY_SSL, True)

        try:
            url = cv.url(url)
        except vol.Invalid:
            errors["base"] = "invalid_url"

        if not errors:
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()
            errors = await _async_validate_connection(
                self.hass,
                url,
                api_key,
                timeout,
                verify_ssl,
            )

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
                errors=errors,
            )

        data: dict[str, Any] = {
            CONF_URL: url,
            CONF_TIMEOUT: timeout,
            CONF_VERIFY_SSL: verify_ssl,
        }
        if api_key:
            data[CONF_API_KEY] = api_key

        return self.async_create_entry(
            title=user_input.get(CONF_NAME, DEFAULT_NAME),
            data=data,
        )


class LemonadeOptionsFlow(config_entries.OptionsFlow):
    """Handle Lemonade Server options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Lemonade Server options."""
        if user_input is not None:
            options = dict(user_input)
            submitted_api_key = options.pop(CONF_API_KEY, None)

            if isinstance(submitted_api_key, str):
                submitted_api_key = submitted_api_key.strip()

            if submitted_api_key:
                if (
                    CONF_API_KEY in self._config_entry.options
                    or submitted_api_key != self._config_entry.data.get(CONF_API_KEY)
                ):
                    options[CONF_API_KEY] = submitted_api_key
            elif CONF_API_KEY in self._config_entry.options:
                existing_api_key = self._config_entry.options[CONF_API_KEY]
                if isinstance(existing_api_key, str):
                    existing_api_key = existing_api_key.strip()
                if existing_api_key:
                    options[CONF_API_KEY] = existing_api_key

            return self.async_create_entry(title="", data=options)

        config_entry = self._config_entry
        api_key = _entry_current_value(config_entry, CONF_API_KEY, "") or ""
        schema: dict[Any, Any] = {
            vol.Optional(
                CONF_API_KEY,
                description={"suggested_value": api_key},
            ): str,
            vol.Required(
                CONF_TIMEOUT,
                default=_entry_current_value(
                    config_entry, CONF_TIMEOUT, DEFAULT_TIMEOUT
                ),
            ): vol.Coerce(float),
            vol.Required(
                CONF_VERIFY_SSL,
                default=_entry_current_value(config_entry, CONF_VERIFY_SSL, True),
            ): cv.boolean,
        }

        for definition in default_model_selector_definitions():
            option_key = definition.option_key
            model_ids = definition.options(config_entry)
            if not model_ids:
                continue
            schema[
                vol.Optional(
                    option_key,
                    default=definition.current_option(config_entry, config_entry),
                )
            ] = _model_select_selector(model_ids)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )


class LemonadeProfileSubentryFlow(config_entries.ConfigSubentryFlow):
    """Handle Lemonade profile subentries."""

    def __init__(self) -> None:
        """Initialize the subentry flow."""
        super().__init__()

    @property
    def _profile_type(self) -> str:
        """Return the requested profile subentry type."""
        context = getattr(self, "context", {})
        context_type = ""
        if isinstance(context, dict):
            context_type = context.get("subentry_type") or context.get("handler") or ""
        return (
            getattr(self, "_subentry_type", None)
            or getattr(self, "subentry_type", None)
            or context_type
        )

    def _async_update_subentry(self, data: dict[str, Any]) -> FlowResult:
        """Update a profile subentry."""
        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            data=data,
        )

    def _profile_schema(
        self,
        definition: ProfileDefinition,
        model_ids: list[str],
        profile_data: dict[str, Any],
    ) -> vol.Schema:
        """Return the schema for a Lemonade profile."""

        def marker(field: Any) -> Any:
            key = field.key
            factory = vol.Required if field.required else vol.Optional
            if key in profile_data:
                return factory(key, default=profile_data[key])
            if field.default is not None:
                return factory(key, default=field.default)
            return factory(key)

        def prompt_marker(field: Any) -> Any:
            if CONF_PROMPT in profile_data:
                return vol.Optional(CONF_PROMPT, default=profile_data[CONF_PROMPT])
            if field.prompt_policy != "default_instructions":
                return vol.Optional(CONF_PROMPT)
            prompt = _default_instructions_prompt()
            if prompt is None:
                return vol.Optional(CONF_PROMPT)
            return vol.Optional(
                CONF_PROMPT,
                description={"suggested_value": prompt},
            )

        schema: dict[Any, Any] = {}
        for field in definition.fields:
            if field.selector_kind == "string":
                schema[marker(field)] = str
            elif field.selector_kind == "model":
                schema[marker(field)] = _model_select_selector(model_ids)
            elif field.selector_kind == "template":
                schema[prompt_marker(field)] = selector.TemplateSelector()
            elif field.selector_kind == "llm_api":
                schema[marker(field)] = selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_llm_api_options(self.hass),
                    )
                )
            elif field.selector_kind == "number" and field.minimum is not None:
                schema[marker(field)] = _number_box_selector(minimum=field.minimum)

        return vol.Schema(schema)

    async def _async_step_profile(
        self,
        step_id: str,
        user_input: dict[str, Any] | None,
        profile_data: dict[str, Any],
        subentry: Any | None = None,
    ) -> FlowResult:
        """Handle profile creation or reconfiguration."""
        config_entry = self._get_entry()
        if (
            getattr(config_entry, "state", None)
            != config_entries.ConfigEntryState.LOADED
        ):
            return self.async_abort(reason="entry_not_loaded")

        profile_type = self._profile_type
        definition = profile_definition(profile_type)
        if definition is None:
            return self.async_abort(reason="unknown_profile_type")

        model_ids = _profile_model_ids(config_entry, definition)
        if not model_ids:
            return self.async_abort(reason="no_models")

        if user_input is not None:
            title = user_input[CONF_NAME]
            if subentry is not None:
                return self._async_update_subentry(user_input)
            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        return self.async_show_form(
            step_id=step_id,
            data_schema=self._profile_schema(definition, model_ids, profile_data),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create a Lemonade profile subentry."""
        return await self._async_step_profile("user", user_input, {})

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Reconfigure a Lemonade profile subentry."""
        subentry = self._get_reconfigure_subentry()
        return await self._async_step_profile(
            "reconfigure",
            user_input,
            dict(getattr(subentry, "data", {}) or {}),
            subentry,
        )
