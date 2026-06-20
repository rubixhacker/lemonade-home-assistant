"""Base entities for Lemonade Server."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import LemonadeCoordinator
from .data import LemonadeConfigEntry


class LemonadeEntity(CoordinatorEntity[LemonadeCoordinator]):
    """Base entity for Lemonade Server platforms."""

    _attr_has_entity_name = True

    def __init__(self, entry: LemonadeConfigEntry, key: str) -> None:
        """Initialize the Lemonade entity."""
        super().__init__(entry.runtime_data.coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
