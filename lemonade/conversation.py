"""Conversation platform for Lemonade Server profiles."""

from __future__ import annotations

import inspect
from typing import Any

from homeassistant.components import conversation
from homeassistant.const import CONF_MODEL
try:
    from homeassistant.const import CONF_PROMPT
except ImportError:  # pragma: no cover - older Home Assistant compatibility
    CONF_PROMPT = "prompt"
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAPABILITY_CONVERSATION,
    CONF_DEFAULT_CONVERSATION_MODEL,
    CONF_LLM_HASS_API,
    DOMAIN,
    SUBENTRY_TYPE_CONVERSATION,
)
from .data import LemonadeConfigEntry
from .llm import async_handle_chat_log


def _subentry_data(subentry: Any) -> dict[str, Any]:
    """Return subentry data as a plain dict."""
    data = getattr(subentry, "data", {}) or {}
    return dict(data) if isinstance(data, dict) else data


def _conversation_subentries(entry: LemonadeConfigEntry) -> list[Any]:
    """Return conversation profile subentries from a config entry."""
    subentries = getattr(entry, "subentries", {}) or {}
    if isinstance(subentries, dict):
        values = subentries.values()
    else:
        values = subentries
    return [
        subentry
        for subentry in values
        if getattr(subentry, "subentry_type", None) == SUBENTRY_TYPE_CONVERSATION
    ]


async def _maybe_await(value: Any) -> None:
    """Await a value only when it is awaitable."""
    if inspect.isawaitable(value):
        await value


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade conversation profile entities."""
    for subentry in _conversation_subentries(entry):
        entity = LemonadeConversationEntity(entry, subentry)
        subentry_id = getattr(subentry, "subentry_id", None)
        if subentry_id is None:
            await _maybe_await(async_add_entities([entity]))
            continue
        try:
            result = async_add_entities([entity], config_subentry_id=subentry_id)
        except TypeError:
            result = async_add_entities([entity])
        await _maybe_await(result)


class LemonadeConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Conversation agent backed by a Lemonade conversation profile."""

    _attr_supports_streaming = False
    _attr_name = None
    _attr_has_entity_name = True
    _attr_supported_features = 0

    def __init__(self, entry: LemonadeConfigEntry, subentry: Any) -> None:
        """Initialize the conversation entity."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = getattr(subentry, "subentry_id")

        entry_id = getattr(entry, "entry_id", None)
        if entry_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry_id)},
                name=getattr(entry, "title", None),
                manufacturer="Lemonade Server",
                entry_type=DeviceEntryType.SERVICE,
            )

        if _subentry_data(subentry).get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> Any:
        """Return supported languages for the conversation agent."""
        return conversation.MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register this entity as the conversation agent for the entry."""
        await _maybe_await(conversation.async_set_agent(self.hass, self.entry, self))

    async def async_will_remove_from_hass(self) -> None:
        """Unregister this entity as the conversation agent for the entry."""
        await _maybe_await(conversation.async_unset_agent(self.hass, self.entry))

    def _resolve_model(self) -> str:
        """Return the model configured for this conversation profile."""
        data = _subentry_data(self.subentry)
        model = data.get(CONF_MODEL)
        if isinstance(model, str) and model:
            return model

        model = getattr(self.entry, "options", {}).get(CONF_DEFAULT_CONVERSATION_MODEL)
        if isinstance(model, str) and model:
            return model

        catalog = self.entry.runtime_data.coordinator.catalog
        first_model = None
        if hasattr(catalog, "first_model_id"):
            first_model = catalog.first_model_id(CAPABILITY_CONVERSATION)
        if first_model is None and hasattr(catalog, "model_ids"):
            model_ids = catalog.model_ids(CAPABILITY_CONVERSATION)
            first_model = model_ids[0] if model_ids else None
        if isinstance(first_model, str) and first_model:
            return first_model

        raise HomeAssistantError("No Lemonade conversation model is available")

    async def _async_handle_message(self, user_input: Any, chat_log: Any) -> Any:
        """Process a conversation message using Lemonade."""
        try:
            model = self._resolve_model()
            data = _subentry_data(self.subentry)
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                data.get(CONF_LLM_HASS_API),
                data.get(CONF_PROMPT),
                user_input.extra_system_prompt,
            )
            await async_handle_chat_log(
                getattr(self, "entity_id", None) or self._attr_unique_id,
                self.entry.runtime_data.client,
                model,
                chat_log,
            )
            return conversation.async_get_result_from_chat_log(user_input, chat_log)
        except conversation.ConverseError as err:
            return err.as_conversation_result()
