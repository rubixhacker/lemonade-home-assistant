from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from .api import LemonadeClient

if TYPE_CHECKING:
    from .coordinator import LemonadeCoordinator


@dataclass
class LemonadeRuntimeData:
    client: LemonadeClient
    coordinator: LemonadeCoordinator


type LemonadeConfigEntry = ConfigEntry[LemonadeRuntimeData]
