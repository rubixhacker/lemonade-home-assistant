"""Data coordinator for Lemonade Server."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class LemonadeRuntimeState:
    """Runtime state for a configured Lemonade Server Entry."""

    health: dict[str, Any]
    raw_models: Any
    catalog: LemonadeModelCatalog
    model_view: RuntimeModelView

    @classmethod
    def from_server_payload(
        cls,
        health: dict[str, Any],
        raw_models: Any,
    ) -> "LemonadeRuntimeState":
        """Build runtime state from Lemonade Server responses."""
        catalog = parse_models_response(raw_models)
        return cls(
            health=health,
            raw_models=raw_models,
            catalog=catalog,
            model_view=RuntimeModelView(catalog),
        )


class LemonadeCoordinator(DataUpdateCoordinator[LemonadeRuntimeState]):
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

    async def _async_update_data(self) -> LemonadeRuntimeState:
        """Fetch Lemonade Server health and models."""
        health = await self.client.health()
        raw_models = await self.client.models()
        return LemonadeRuntimeState.from_server_payload(health, raw_models)

    @property
    def runtime_state(self) -> LemonadeRuntimeState | None:
        """Return the latest Server Entry runtime state."""
        return self.data if isinstance(self.data, LemonadeRuntimeState) else None

    @property
    def health(self) -> dict[str, Any]:
        """Return the latest Lemonade Server health."""
        return self.runtime_state.health if self.runtime_state is not None else {}

    @property
    def catalog(self) -> LemonadeModelCatalog:
        """Return the latest parsed Lemonade model catalog."""
        if self.runtime_state is not None:
            return self.runtime_state.catalog
        return parse_models_response({})

    @property
    def model_view(self) -> RuntimeModelView:
        """Return the latest runtime model view."""
        if self.runtime_state is not None:
            return self.runtime_state.model_view
        return RuntimeModelView(self.catalog)

    @property
    def server_status(self) -> str | None:
        """Return the latest Lemonade Server status string."""
        status = self.health.get("status")
        return status if isinstance(status, str) else None
