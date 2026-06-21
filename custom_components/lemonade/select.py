"""Select entities for Lemonade Server."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import LemonadeConfigEntry
from .entity import LemonadeEntity
from .server_capabilities import (
    DefaultModelSelectorDefinition,
    default_model_selector_definitions,
    runtime_model_view,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server model selects."""
    async_add_entities(
        [
            LemonadeDefaultModelSelect(
                entry,
                definition,
            )
            for definition in default_model_selector_definitions()
        ]
    )


class LemonadeDefaultModelSelect(LemonadeEntity, SelectEntity):
    """Select the default Lemonade model for a capability."""

    def __init__(
        self,
        entry: LemonadeConfigEntry,
        selector_definition: DefaultModelSelectorDefinition,
    ) -> None:
        """Initialize the default model select."""
        super().__init__(entry, selector_definition.option_key)
        self.selector_definition = selector_definition
        self._attr_name = selector_definition.name
        self._attr_translation_key = selector_definition.option_key

    @property
    def options(self) -> list[str]:
        """Return available model IDs for the capability."""
        return runtime_model_view(self.coordinator).default_model_selector_options(
            self.selector_definition
        )

    @property
    def current_option(self) -> str | None:
        """Return the configured model or the first available model."""
        model_view = runtime_model_view(self.coordinator)
        return model_view.current_default_model_selector_option(
            self.entry, self.selector_definition
        )

    @property
    def available(self) -> bool:
        """Return true when at least one model option is available."""
        return bool(self.options) and super().available

    async def async_select_option(self, option: str) -> None:
        """Update the configured default model and reload the entry."""
        option = runtime_model_view(
            self.coordinator
        ).validate_default_model_selector_option(option, self.selector_definition)
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, self.selector_definition.option_key: option},
        )
        await self.hass.config_entries.async_reload(self.entry.entry_id)
