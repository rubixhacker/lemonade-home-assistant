"""Sensor entities for Lemonade Server."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODEL_COUNT_SENSOR_NAMES
from .data import LemonadeConfigEntry
from .entity import LemonadeEntity
from .server_capabilities import (
    ModelCountSensorPolicy,
    model_count_sensor_policies,
    runtime_model_view,
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
                LemonadeCapabilityCountSensor(
                    entry,
                    policy,
                )
                for policy in model_count_sensor_policies()
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
        self._attr_name = MODEL_COUNT_SENSOR_NAMES["server_status"]

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
        self._attr_name = MODEL_COUNT_SENSOR_NAMES["model_count"]

    @property
    def native_value(self) -> int:
        """Return the total parsed model count."""
        return runtime_model_view(self.coordinator).total_model_count


class LemonadeCapabilityCountSensor(LemonadeSensor):
    """Report the model count for one Lemonade capability."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: LemonadeConfigEntry,
        policy: ModelCountSensorPolicy,
    ) -> None:
        """Initialize the capability count sensor."""
        super().__init__(entry, policy.translation_key)
        self._policy = policy
        self._attr_name = MODEL_COUNT_SENSOR_NAMES.get(
            policy.translation_key,
            policy.translation_key,
        )
        self._attr_translation_key = policy.translation_key

    @property
    def native_value(self) -> int:
        """Return the model count for the capability."""
        return runtime_model_view(self.coordinator).model_count(self._policy.capability)
