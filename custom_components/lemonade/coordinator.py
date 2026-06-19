"""Data coordinator for Lemonade Server."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import LemonadeClient
from .const import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN
from .model_resolution import RuntimeModelView
from .models import LemonadeModelCatalog, parse_models_response

_LOGGER = logging.getLogger(__name__)


class LemonadeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Lemonade Server health and model catalog updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: LemonadeClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch Lemonade Server health and models."""
        health = await self.client.health()
        raw_models = await self.client.models()
        return {
            "health": health,
            "models": raw_models,
            "catalog": parse_models_response(raw_models),
        }

    @property
    def health(self) -> dict[str, Any]:
        """Return the latest Lemonade Server health."""
        if not self.data:
            return {}
        health = self.data.get("health")
        return health if isinstance(health, dict) else {}

    @property
    def catalog(self) -> LemonadeModelCatalog:
        """Return the latest parsed Lemonade model catalog."""
        if self.data:
            catalog = self.data.get("catalog")
            if isinstance(catalog, LemonadeModelCatalog):
                return catalog
        return parse_models_response({})

    @property
    def model_view(self) -> RuntimeModelView:
        """Return the latest runtime model view."""
        return RuntimeModelView(self.catalog)

    @property
    def server_status(self) -> str | None:
        """Return the latest Lemonade Server status string."""
        status = self.health.get("status")
        return status if isinstance(status, str) else None
