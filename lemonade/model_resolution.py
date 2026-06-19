"""Lemonade model resolution policy."""

from __future__ import annotations

from typing import Any


def _model_id(value: Any) -> str | None:
    """Return a non-empty model ID."""
    if isinstance(value, str) and value:
        return value
    return None


def catalog_model_ids(catalog: Any, capability: str) -> list[str]:
    """Return catalog model IDs for a capability."""
    if hasattr(catalog, "model_ids"):
        return [
            model_id
            for model_id in catalog.model_ids(capability)
            if isinstance(model_id, str) and model_id
        ]
    if hasattr(catalog, "models_for"):
        return [
            model_id
            for model in catalog.models_for(capability)
            if (model_id := _model_id(getattr(model, "id", None))) is not None
        ]
    return []


def first_catalog_model_id(catalog: Any, capability: str) -> str | None:
    """Return the first compatible model ID for a capability."""
    if hasattr(catalog, "first_model_id"):
        model = _model_id(catalog.first_model_id(capability))
        if model is not None:
            return model

    model_ids = catalog_model_ids(catalog, capability)
    return model_ids[0] if model_ids else None


def resolve_model(
    catalog: Any,
    capability: str,
    *,
    explicit_model: Any = None,
    profile_model: Any = None,
    default_model: Any = None,
) -> str | None:
    """Resolve a model using explicit, profile, default, then catalog policy."""
    for model in (explicit_model, profile_model, default_model):
        if resolved := _model_id(model):
            return resolved
    return first_catalog_model_id(catalog, capability)


def resolve_entry_model(
    entry: Any,
    capability: str,
    *,
    explicit_model: Any = None,
    profile_model: Any = None,
    default_option: str | None = None,
) -> str | None:
    """Resolve a model for a config entry and capability."""
    default_model = None
    if default_option is not None:
        default_model = getattr(entry, "options", {}).get(default_option)

    return resolve_model(
        entry.runtime_data.coordinator.catalog,
        capability,
        explicit_model=explicit_model,
        profile_model=profile_model,
        default_model=default_model,
    )
