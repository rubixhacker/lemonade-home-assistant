"""Repairs helpers for Lemonade Server."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN


def async_delete_missing_capability_issue(
    hass: HomeAssistant, entry_id: str, capability: str
) -> None:
    """Delete a repair issue for a restored model capability."""
    ir.async_delete_issue(hass, DOMAIN, f"missing_{capability}_{entry_id}")
