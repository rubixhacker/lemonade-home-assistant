"""End-to-end regressions for upstream timeout and profile behavior."""

from typing import Any

from homeassistant.components.conversation.const import (
    ATTR_AGENT_ID,
    ATTR_TEXT,
    DOMAIN as CONVERSATION_DOMAIN,
    SERVICE_PROCESS,
)
from homeassistant.const import CONF_MODEL, CONF_NAME, CONF_TIMEOUT

from custom_components.lemonade.const import (
    CONF_INFERENCE_TIMEOUT,
    DOMAIN,
    SUBENTRY_TYPE_CONVERSATION,
)
from tests.e2e.test_v1_1_features import _create_profile, _profile_entity_id


async def test_explicit_inference_timeout_survives_reload(
    hass: Any,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """An explicitly configured inference timeout is used by the client."""
    entry, _, _ = lemonade_entry
    data = {**entry.data, CONF_INFERENCE_TIMEOUT: 42.0}
    hass.config_entries.async_update_entry(entry, data=data)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.client.inference_timeout == 42.0


async def test_long_connection_timeout_raises_default_inference_budget(
    hass: Any,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """A longer connection timeout also gets a suitable inference budget."""
    entry, _, _ = lemonade_entry
    hass.config_entries.async_update_entry(
        entry,
        data={key: value for key, value in entry.data.items() if key != CONF_INFERENCE_TIMEOUT},
        options={CONF_TIMEOUT: 900.0},
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.client.inference_timeout == 900.0


async def test_persisted_profile_model_alias_is_forwarded_without_catalog_entry(
    hass: Any,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """A persisted profile keeps using a model absent from the refreshed catalog."""
    entry, _, requests = lemonade_entry
    profile = await _create_profile(
        hass,
        entry,
        SUBENTRY_TYPE_CONVERSATION,
        {
            CONF_NAME: "Legacy model profile",
            CONF_MODEL: "local-chat",
        },
    )
    assert hass.config_entries.async_update_subentry(
        entry,
        profile,
        data={**profile.data, CONF_MODEL: "extra.chat"},
    )
    await hass.async_block_till_done()
    profile = next(item for item in entry.subentries.values() if item.subentry_id == profile.subentry_id)
    entity_id = _profile_entity_id(hass, entry, profile, CONVERSATION_DOMAIN)
    await hass.services.async_call(
        CONVERSATION_DOMAIN,
        SERVICE_PROCESS,
        {ATTR_AGENT_ID: entity_id, ATTR_TEXT: "Hello"},
        blocking=True,
        return_response=True,
    )
    chat = [item for item in requests if item["path"] == "/v1/chat/completions"][-1]
    assert chat["payload"]["model"] == "extra.chat"
