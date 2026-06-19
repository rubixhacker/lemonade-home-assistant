"""Select entities for Lemonade Server."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEFAULT_MODEL,
    DEFAULT_MODEL_OPTION_NAMES,
    default_model_capability_presentations,
)
from .data import LemonadeConfigEntry
from .entity import LemonadeEntity
from .model_resolution import runtime_model_view


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server model selects."""
    async_add_entities(
        [LemonadeDefaultModelSelect(entry, None, CONF_DEFAULT_MODEL)]
        + [
            LemonadeDefaultModelSelect(
                entry,
                presentation.capability,
                presentation.default_option_key,
            )
            for presentation in default_model_capability_presentations()
            if presentation.default_option_key is not None
        ]
    )


class LemonadeDefaultModelSelect(LemonadeEntity, SelectEntity):
    """Select the default Lemonade model for a capability."""

    def __init__(
        self,
        entry: LemonadeConfigEntry,
        capability: str | None,
        option_key: str,
    ) -> None:
        """Initialize the default model select."""
        super().__init__(entry, option_key)
        self._capability = capability
        self._option_key = option_key
        self._attr_name = DEFAULT_MODEL_OPTION_NAMES.get(option_key, option_key)
        self._attr_translation_key = option_key

    @property
    def options(self) -> list[str]:
        """Return available model IDs for the capability."""
        model_view = runtime_model_view(self.coordinator)
        if self._capability is None:
            return model_view.all_model_ids
        return model_view.model_ids(self._capability) or model_view.all_model_ids

    @property
    def current_option(self) -> str | None:
        """Return the configured model or the first available model."""
        if self._capability is None:
            model_view = runtime_model_view(self.coordinator)
            configured = model_view.entry_default_model(self.entry, self._option_key)
            options = self.options
            if configured in options:
                return configured
            return options[0] if options else None
        return runtime_model_view(self.coordinator).current_entry_model_option(
            self.entry,
            self._capability,
            self._option_key,
        )

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
