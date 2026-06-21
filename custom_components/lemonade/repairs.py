"""Repairs helpers for Lemonade Server."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .server_capabilities import MissingCapabilityRepairIssueIdentity


def async_delete_missing_capability_issue(
    hass: HomeAssistant, entry_id: str, capability: str
) -> None:
    """Delete a repair issue for a restored model capability."""
    async_delete_missing_capability_issue_identity(
        hass,
        entry_id,
        MissingCapabilityRepairIssueIdentity(capability),
    )


def async_delete_missing_capability_issue_identity(
    hass: HomeAssistant,
    entry_id: str,
    identity: MissingCapabilityRepairIssueIdentity,
) -> None:
    """Delete a repair issue by typed Server Entry repair identity."""
    ir.async_delete_issue(hass, DOMAIN, identity.issue_id(entry_id))
