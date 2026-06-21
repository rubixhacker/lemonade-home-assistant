"""Compatibility wrappers for Lemonade model resolution policy."""

from __future__ import annotations

from typing import Any

from .models import Capability
from .server_capabilities import (
    RuntimeCapabilityView,
    RuntimeModelView,
    catalog_all_model_ids,
    catalog_model_ids,
    first_catalog_model_id,
    runtime_model_view,
)

__all__ = (
    "RuntimeCapabilityView",
    "RuntimeModelView",
    "catalog_all_model_ids",
    "catalog_model_ids",
    "first_catalog_model_id",
    "resolve_entry_model",
    "resolve_model",
    "runtime_model_view",
)


def resolve_model(
    catalog: Any,
    capability: Capability | str,
    *,
    explicit_model: Any = None,
    profile_model: Any = None,
    default_model: Any = None,
) -> str | None:
    """Resolve a model using explicit, profile, default, then catalog policy."""
    return RuntimeCapabilityView(catalog).resolve_model(
        capability,
        explicit_model=explicit_model,
        profile_model=profile_model,
        default_model=default_model,
    )


def resolve_entry_model(
    entry: Any,
    capability: Capability | str,
    *,
    explicit_model: Any = None,
    profile_model: Any = None,
    default_option: str | None = None,
) -> str | None:
    """Resolve a model for a config entry and capability."""
    return runtime_model_view(entry).resolve_entry_model(
        entry,
        capability,
        explicit_model=explicit_model,
        profile_model=profile_model,
        default_option=default_option,
    )
