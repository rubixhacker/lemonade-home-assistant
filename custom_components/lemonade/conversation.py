"""Conversation platform for Lemonade Server profiles."""

from __future__ import annotations

from typing import Any

from homeassistant.components import conversation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SUBENTRY_TYPE_CONVERSATION,
)
from .data import LemonadeConfigEntry
from . import profile_chat
from .profiles import (
    ConversationProfile,
    async_add_profile_entity,
    parse_conversation_profile,
    profile_subentries,
    profile_title,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade conversation profile entities."""
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

        if self._attr_unique_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, self._attr_unique_id)},
                name=profile_title(subentry, getattr(entry, "title", None)),
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
        return parse_conversation_profile(self.subentry)

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

    async def _async_handle_message(self, user_input: Any, chat_log: Any) -> Any:
        """Process a conversation message using Lemonade."""
        try:
            await profile_chat.async_execute_conversation_profile_turn(
                entry=self.entry,
                profile=self.profile,
                entity_id=getattr(self, "entity_id", None) or self._attr_unique_id,
                user_input=user_input,
                chat_log=chat_log,
            )
            return conversation.async_get_result_from_chat_log(user_input, chat_log)
        except conversation.ConverseError as err:
            return err.as_conversation_result()
