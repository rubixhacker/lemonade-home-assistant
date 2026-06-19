"""Select entities for Lemonade Server."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_DEFAULT_AI_TASK_MODEL,
    CONF_DEFAULT_CONVERSATION_MODEL,
    CONF_DEFAULT_IMAGE_MODEL,
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
)
from .data import LemonadeConfigEntry
from .entity import LemonadeEntity

_DEFAULT_MODEL_SELECTS = (
    (CAPABILITY_CONVERSATION, CONF_DEFAULT_CONVERSATION_MODEL),
    (CAPABILITY_AI_TASK, CONF_DEFAULT_AI_TASK_MODEL),
    (CAPABILITY_IMAGE, CONF_DEFAULT_IMAGE_MODEL),
    (CAPABILITY_TTS, CONF_DEFAULT_TTS_MODEL),
    (CAPABILITY_STT, CONF_DEFAULT_STT_MODEL),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server model selects."""
    async_add_entities(
        [
            LemonadeDefaultModelSelect(entry, capability, option_key)
            for capability, option_key in _DEFAULT_MODEL_SELECTS
        ]
    )


class LemonadeDefaultModelSelect(LemonadeEntity, SelectEntity):
    """Select the default Lemonade model for a capability."""

    def __init__(
        self,
        entry: LemonadeConfigEntry,
        capability: str,
        option_key: str,
    ) -> None:
        """Initialize the default model select."""
        super().__init__(entry, option_key)
        self._capability = capability
        self._option_key = option_key
        self._attr_translation_key = option_key

    @property
    def options(self) -> list[str]:
        """Return available model IDs for the capability."""
        return self.coordinator.catalog.model_ids(self._capability)

    @property
    def current_option(self) -> str | None:
        """Return the configured model or the first available model."""
        options = self.options
        configured = self.entry.options.get(
            self._option_key,
            self.entry.data.get(self._option_key),
        )
        if isinstance(configured, str) and configured in options:
            return configured
        return options[0] if options else None

    @property
    def available(self) -> bool:
        """Return true when at least one model option is available."""
        return bool(self.options) and super().available

    async def async_select_option(self, option: str) -> None:
        """Update the configured default model and reload the entry."""
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, self._option_key: option},
        )
        await self.hass.config_entries.async_reload(self.entry.entry_id)
