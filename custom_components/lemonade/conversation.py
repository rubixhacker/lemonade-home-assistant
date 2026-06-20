"""Conversation platform for Lemonade Server profiles."""

from __future__ import annotations

from typing import Any

from homeassistant.components import conversation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAPABILITY_CONVERSATION,
    CONF_DEFAULT_CONVERSATION_MODEL,
    DOMAIN,
    SUBENTRY_TYPE_CONVERSATION,
)
from .data import LemonadeConfigEntry
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .llm import async_execute_chat_log_turn
from .model_resolution import resolve_entry_model
from .profiles import (
    ConversationProfile,
    async_add_profile_entity,
    parse_profile,
    profile_subentries,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade conversation entities."""
    await async_add_profile_entity(
        async_add_entities,
        LemonadeConversationEntity(entry),
        None,
    )
    for subentry in profile_subentries(entry, SUBENTRY_TYPE_CONVERSATION):
        entity = LemonadeConversationEntity(entry, subentry)
        await async_add_profile_entity(
            async_add_entities,
            entity,
            getattr(subentry, "subentry_id", None),
        )


class LemonadeConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Conversation agent backed by Lemonade Server."""

    _attr_supports_streaming = False
    _attr_name = None
    _attr_has_entity_name = True
    _attr_supported_features = 0

    def __init__(self, entry: LemonadeConfigEntry, subentry: Any = None) -> None:
        """Initialize the conversation entity."""
        self.entry = entry
        self.subentry = subentry
        subentry_id = getattr(subentry, "subentry_id", None)
        entry_id = getattr(entry, "entry_id", None)
        if subentry_id is not None:
            self._attr_unique_id = subentry_id
        elif entry_id:
            self._attr_unique_id = f"{entry_id}_conversation"
        else:
            self._attr_unique_id = SUBENTRY_TYPE_CONVERSATION

        if entry_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry_id)},
                name=getattr(entry, "title", None),
                manufacturer="Lemonade Server",
                entry_type=DeviceEntryType.SERVICE,
            )

    @property
    def supported_languages(self) -> Any:
        """Return supported languages for the conversation agent."""
        return conversation.MATCH_ALL

    @property
    def profile(self) -> ConversationProfile:
        """Return the current parsed conversation profile."""
        profile = parse_profile(self.subentry, SUBENTRY_TYPE_CONVERSATION)
        assert isinstance(profile, ConversationProfile)
        return profile

    @property
    def supported_features(self) -> Any:
        """Return supported features for the current conversation profile."""
        if self.profile.hass_api:
            return conversation.ConversationEntityFeature.CONTROL
        return 0

    async def async_added_to_hass(self) -> None:
        """Register this entity as the conversation agent for the entry."""
        result = conversation.async_set_agent(self.hass, self.entry, self)
        if hasattr(result, "__await__"):
            await result

    async def async_will_remove_from_hass(self) -> None:
        """Unregister this entity as the conversation agent for the entry."""
        result = conversation.async_unset_agent(self.hass, self.entry)
        if hasattr(result, "__await__"):
            await result

    def _resolve_model(self) -> str:
        """Return the model configured for this conversation profile."""
        model = resolve_entry_model(
            self.entry,
            CAPABILITY_CONVERSATION,
            profile_model=self.profile.model,
            default_option=CONF_DEFAULT_CONVERSATION_MODEL,
        )
        if model is not None:
            return model

        raise HomeAssistantError("No Lemonade conversation model is available")

    async def _async_handle_message(self, user_input: Any, chat_log: Any) -> Any:
        """Process a conversation message using Lemonade."""
        try:
            model = self._resolve_model()
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                self.profile.hass_api,
                self.profile.prompt,
                user_input.extra_system_prompt,
            )
            try:
                await async_execute_chat_log_turn(
                    entity_id=getattr(self, "entity_id", None)
                    or self._attr_unique_id,
                    client=self.entry.runtime_data.client,
                    model=model,
                    chat_log=chat_log,
                )
            except LEMONADE_CLIENT_EXCEPTIONS as err:
                raise lemonade_home_assistant_error(
                    err,
                    "Error talking to Lemonade Server",
                    timeout_message=None,
                ) from err
            return conversation.async_get_result_from_chat_log(user_input, chat_log)
        except conversation.ConverseError as err:
            return err.as_conversation_result()
