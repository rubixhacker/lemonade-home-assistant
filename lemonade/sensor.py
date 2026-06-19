"""Sensor entities for Lemonade Server."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAPABILITY_CONVERSATION,
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
)
from .data import LemonadeConfigEntry
from .entity import LemonadeEntity

_CAPABILITY_COUNT_SENSORS = (
    (CAPABILITY_CONVERSATION, "conversation_model_count"),
    (CAPABILITY_IMAGE, "image_model_count"),
    (CAPABILITY_TTS, "tts_model_count"),
    (CAPABILITY_STT, "stt_model_count"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server sensors."""
    async_add_entities(
        [
            LemonadeServerStatusSensor(entry),
            LemonadeTotalModelCountSensor(entry),
            *(
                LemonadeCapabilityCountSensor(entry, capability, translation_key)
                for capability, translation_key in _CAPABILITY_COUNT_SENSORS
            ),
        ]
    )


class LemonadeSensor(LemonadeEntity, SensorEntity):
    """Base class for Lemonade Server sensors."""


class LemonadeServerStatusSensor(LemonadeSensor):
    """Report whether the Lemonade Server coordinator is online."""

    _attr_translation_key = "server_status"

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the server status sensor."""
        super().__init__(entry, "server_status")

    @property
    def native_value(self) -> str:
        """Return the server status."""
        return "online" if self.coordinator.last_update_success else "offline"

    @property
    def available(self) -> bool:
        """Keep the status sensor available so it can report offline."""
        return True


class LemonadeTotalModelCountSensor(LemonadeSensor):
    """Report the total parsed Lemonade model count."""

    _attr_translation_key = "model_count"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the model count sensor."""
        super().__init__(entry, "model_count")

    @property
    def native_value(self) -> int:
        """Return the total parsed model count."""
        return len(self.coordinator.catalog.models)


class LemonadeCapabilityCountSensor(LemonadeSensor):
    """Report the model count for one Lemonade capability."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: LemonadeConfigEntry,
        capability: str,
        translation_key: str,
    ) -> None:
        """Initialize the capability count sensor."""
        super().__init__(entry, translation_key)
        self._capability = capability
        self._attr_translation_key = translation_key

    @property
    def native_value(self) -> int:
        """Return the model count for the capability."""
        return len(self.coordinator.catalog.models_for(self._capability))
