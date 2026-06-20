"""Lemonade model resolution policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .models import Capability, ModelId, parse_models_response


def _model_id(value: Any) -> str | None:
    """Return a non-empty model ID."""
    model_id = ModelId.parse(value)
    return str(model_id) if model_id is not None else None


def _capability(value: Any) -> Capability | None:
    """Return a known model capability."""
    return Capability.parse(value)


def catalog_model_ids(catalog: Any, capability: Capability | str) -> list[str]:
    """Return catalog model IDs for a capability."""
    parsed_capability = _capability(capability)
    if parsed_capability is None:
        return []

    if hasattr(catalog, "model_ids"):
        return [
            str(model_id)
            for model_id in (
                ModelId.parse(model_id)
                for model_id in catalog.model_ids(parsed_capability)
            )
            if model_id is not None
        ]
    if hasattr(catalog, "models_for"):
        return [
            model_id
            for model in catalog.models_for(parsed_capability)
            if (model_id := _model_id(getattr(model, "id", None))) is not None
        ]
    return []


def catalog_all_model_ids(catalog: Any) -> list[str]:
    """Return every usable model ID in catalog order."""
    if hasattr(catalog, "all_model_ids"):
        return [
            str(model_id)
            for model_id in (
                ModelId.parse(model_id) for model_id in catalog.all_model_ids
            )
            if model_id is not None
        ]

    models = getattr(catalog, "models", ())
    return [
        model_id
        for model in models
        if (model_id := _model_id(getattr(model, "id", None))) is not None
    ]


def first_catalog_model_id(catalog: Any, capability: Capability | str) -> str | None:
    """Return the first compatible model ID for a capability."""
    parsed_capability = _capability(capability)
    if parsed_capability is None:
        return None

    if hasattr(catalog, "first_model_id"):
        model = _model_id(catalog.first_model_id(parsed_capability))
        if model is not None:
            return model

    model_ids = catalog_model_ids(catalog, parsed_capability)
    return model_ids[0] if model_ids else None


def _entry_default_model(entry: Any, option_key: str | None) -> str | None:
    """Return the configured entry default model from options or data."""
    if option_key is None:
        return None

    for values in (
        getattr(entry, "options", None),
        getattr(entry, "data", None),
    ):
        if isinstance(values, Mapping):
            model = _model_id(values.get(option_key))
            if model is not None:
                return model
    return None


@dataclass(frozen=True, slots=True)
class RuntimeModelView:
    """Runtime model and selection view for a Lemonade config entry."""

    catalog: Any

    @property
    def total_model_count(self) -> int:
        """Return the total number of parsed runtime models."""
        models = getattr(self.catalog, "models", ())
        try:
            return len(models)
        except TypeError:
            return 0

    def model_ids(self, capability: Capability | str) -> list[str]:
        """Return model IDs available for a capability."""
        return catalog_model_ids(self.catalog, capability)

    @property
    def all_model_ids(self) -> list[str]:
        """Return all model IDs available from Lemonade."""
        return catalog_all_model_ids(self.catalog)

    def model_count(self, capability: Capability | str) -> int:
        """Return the number of models available for a capability."""
        return len(self.model_ids(capability))

    def has_models(self, capability: Capability | str) -> bool:
        """Return true when the capability has at least one model."""
        return bool(self.model_ids(capability))

    def first_model_id(self, capability: Capability | str) -> str | None:
        """Return the first available model for a capability."""
        return first_catalog_model_id(self.catalog, capability)

    def entry_default_model(self, entry: Any, option_key: str | None) -> str | None:
        """Return a configured entry default model from options or data."""
        return _entry_default_model(entry, option_key)

    def resolve_model(
        self,
        capability: Capability | str,
        *,
        explicit_model: Any = None,
        profile_model: Any = None,
        default_model: Any = None,
    ) -> str | None:
        """Resolve a model using explicit, profile, default, then catalog policy."""
        for model in (explicit_model, profile_model, default_model):
            if resolved := _model_id(model):
                return resolved
        return self.first_model_id(capability)

    def resolve_entry_model(
        self,
        entry: Any,
        capability: Capability | str,
        *,
        explicit_model: Any = None,
        profile_model: Any = None,
        default_option: str | None = None,
    ) -> str | None:
        """Resolve a model for a config entry and capability."""
        return self.resolve_model(
            capability,
            explicit_model=explicit_model,
            profile_model=profile_model,
            default_model=self.entry_default_model(entry, default_option),
        )

    def current_entry_model_option(
        self,
        entry: Any,
        capability: Capability | str,
        option_key: str,
    ) -> str | None:
        """Return the valid selected model option or first available model."""
        options = self.model_ids(capability)
        if not options:
            options = self.all_model_ids
        configured = self.entry_default_model(entry, option_key)
        if configured in options:
            return configured
        return options[0] if options else None


def runtime_model_view(source: Any) -> RuntimeModelView:
    """Return a runtime model view for an entry, coordinator, catalog, or view."""
    if isinstance(source, RuntimeModelView):
        return source

    runtime_data = getattr(source, "runtime_data", None)
    if runtime_data is not None:
        return runtime_model_view(getattr(runtime_data, "coordinator", None))

    view = getattr(source, "model_view", None)
    if isinstance(view, RuntimeModelView):
        return view

    catalog = getattr(source, "catalog", None)
    if catalog is not None:
        return RuntimeModelView(catalog)

    return RuntimeModelView(parse_models_response({}))


def resolve_model(
    catalog: Any,
    capability: Capability | str,
    *,
    explicit_model: Any = None,
    profile_model: Any = None,
    default_model: Any = None,
) -> str | None:
    """Resolve a model using explicit, profile, default, then catalog policy."""
    return RuntimeModelView(catalog).resolve_model(
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
