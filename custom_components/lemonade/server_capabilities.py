"""Server Entry capability policy and runtime decisions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .const import (
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
)
from .models import Capability, LemonadeModelCatalog, ModelId


class ModelSelectorDegradedPolicy(StrEnum):
    """Closed fallback behavior for Server Entry Model Selectors."""

    FALLBACK_TO_ALL_MODELS = "fallback_to_all_models"
    CAPABILITY_MODELS_ONLY = "capability_models_only"


@dataclass(frozen=True, slots=True)
class ModelCountSensorPolicy:
    """Policy for a Server Entry model-count sensor."""

    capability: Capability
    translation_key: str


@dataclass(frozen=True, slots=True)
class DefaultModelSelectorDefinition:
    """Policy for a Server Entry default Model Selector."""

    capability: Capability
    option_key: str
    name: str
    degraded_policy: ModelSelectorDegradedPolicy = (
        ModelSelectorDegradedPolicy.FALLBACK_TO_ALL_MODELS
    )

    def options(self, source: object) -> list[str]:
        """Return selectable model IDs for this selector."""
        return runtime_model_view(source).default_model_selector_options(self)

    def current_option(self, entry: object, source: object) -> str | None:
        """Return the configured valid option or the first selectable model."""
        return runtime_model_view(source).current_default_model_selector_option(
            entry,
            self,
        )

    def validate_option(self, option: str, source: object) -> str:
        """Return a valid selectable option or raise."""
        return runtime_model_view(source).validate_default_model_selector_option(
            option,
            self,
        )


@dataclass(frozen=True, slots=True)
class MissingCapabilityRepairIssueIdentity:
    """Repair issue identity for a missing Server Entry capability."""

    capability: Capability

    def issue_id(self, entry_id: str) -> str:
        """Return the stable Home Assistant repair issue ID."""
        return f"missing_{self.capability}_{entry_id}"


@dataclass(frozen=True, slots=True)
class CapabilityPresentation:
    """Compatibility presentation metadata for a Lemonade model capability."""

    capability: Capability
    default_option_key: str | None = None
    model_count_translation_key: str | None = None
    repair_issue: bool = False


@dataclass(frozen=True, slots=True)
class CapabilityDescription:
    """Semantic Home Assistant presentation for one known capability."""

    capability: Capability
    default_option_key: str | None = None
    selector_name: str | None = None
    model_count_translation_key: str | None = None
    repair_issue: bool = False
    degraded_policy: ModelSelectorDegradedPolicy = (
        ModelSelectorDegradedPolicy.FALLBACK_TO_ALL_MODELS
    )

    def to_presentation(self) -> CapabilityPresentation:
        """Project compatibility presentation metadata."""
        return CapabilityPresentation(
            self.capability,
            self.default_option_key,
            self.model_count_translation_key,
            self.repair_issue,
        )


CAPABILITY_DESCRIPTIONS = (
    CapabilityDescription(
        Capability.CONVERSATION,
        model_count_translation_key="conversation_model_count",
    ),
    CapabilityDescription(Capability.AI_TASK),
    CapabilityDescription(Capability.TOOL_CALLING),
    CapabilityDescription(Capability.VISION),
    CapabilityDescription(
        Capability.IMAGE,
        model_count_translation_key="image_model_count",
        repair_issue=True,
    ),
    CapabilityDescription(Capability.IMAGE_EDIT),
    CapabilityDescription(
        Capability.TTS,
        default_option_key=CONF_DEFAULT_TTS_MODEL,
        selector_name="Default text-to-speech model",
        model_count_translation_key="tts_model_count",
        repair_issue=True,
    ),
    CapabilityDescription(
        Capability.STT,
        default_option_key=CONF_DEFAULT_STT_MODEL,
        selector_name="Default speech-to-text model",
        model_count_translation_key="stt_model_count",
        repair_issue=True,
    ),
    CapabilityDescription(Capability.EMBEDDINGS),
)


def _model_id(value: Any) -> str | None:
    """Return a non-empty model ID."""
    model_id = ModelId.parse(value)
    return str(model_id) if model_id is not None else None


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


def _is_default_model_selector_option(option_key: str | None) -> bool:
    """Return true when an option key is backed by Model Selector policy."""
    return option_key in {
        definition.option_key for definition in default_model_selector_definitions()
    }


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityView:
    """Runtime model and selection view for a Lemonade Server Entry."""

    catalog: LemonadeModelCatalog

    @property
    def total_model_count(self) -> int:
        """Return the total number of parsed runtime models."""
        return len(self.catalog.models)

    def model_ids(self, capability: Capability | str) -> list[str]:
        """Return model IDs available for a capability."""
        return self.catalog.model_ids(capability)

    @property
    def all_model_ids(self) -> list[str]:
        """Return all model IDs available from Lemonade."""
        return self.catalog.all_model_ids

    def model_count(self, capability: Capability | str) -> int:
        """Return the number of models available for a capability."""
        return len(self.model_ids(capability))

    def has_models(self, capability: Capability | str) -> bool:
        """Return true when the capability has at least one model."""
        return bool(self.model_ids(capability))

    def has_capability_models(self, capability: Capability | str) -> bool:
        """Return true when the capability has at least one model."""
        return self.has_models(capability)

    def first_model_id(self, capability: Capability | str) -> str | None:
        """Return the first available model for a capability."""
        return self.catalog.first_model_id(capability)

    def default_model_selector_options(
        self,
        policy: DefaultModelSelectorDefinition,
    ) -> list[str]:
        """Return selectable model IDs for a Server Entry Model Selector."""
        capability_options = self.model_ids(policy.capability)
        if (
            capability_options
            or policy.degraded_policy
            != ModelSelectorDegradedPolicy.FALLBACK_TO_ALL_MODELS
        ):
            return capability_options
        return self.all_model_ids

    def entry_default_model(self, entry: Any, option_key: str | None) -> str | None:
        """Return a configured entry default model from options or data."""
        return _entry_default_model(entry, option_key)

    def current_default_model_selector_option(
        self,
        entry: Any,
        policy: DefaultModelSelectorDefinition,
    ) -> str | None:
        """Return the valid selected Model Selector option or first option."""
        options = self.default_model_selector_options(policy)
        configured = self.entry_default_model(entry, policy.option_key)
        if configured in options:
            return configured
        return options[0] if options else None

    def validate_default_model_selector_option(
        self,
        option: str,
        policy: DefaultModelSelectorDefinition,
    ) -> str:
        """Return a valid Model Selector option or raise."""
        if option not in self.default_model_selector_options(policy):
            raise ValueError(f"Unknown Lemonade model option: {option}")
        return option

    def valid_entry_default_model(
        self,
        entry: Any,
        capability: Capability | str,
        option_key: str | None,
    ) -> str | None:
        """Return the configured entry default when valid for runtime resolution."""
        configured = self.entry_default_model(entry, option_key)
        if configured is None:
            return None

        if not _is_default_model_selector_option(option_key):
            return configured

        capability_options = self.model_ids(capability)
        if capability_options and configured not in capability_options:
            return None
        return configured

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
            default_model=self.valid_entry_default_model(
                entry,
                capability,
                default_option,
            ),
        )

    def current_entry_model_option(
        self,
        entry: Any,
        capability: Capability | str,
        option_key: str,
    ) -> str | None:
        """Return the valid selected model option or first available model."""
        policy = default_model_selector_definition(option_key)
        if policy is not None:
            return self.current_default_model_selector_option(entry, policy)

        options = self.model_ids(capability)
        if not options:
            options = self.all_model_ids
        configured = self.entry_default_model(entry, option_key)
        if configured in options:
            return configured
        return options[0] if options else None


RuntimeModelView = RuntimeCapabilityView


def runtime_model_view(source: object) -> RuntimeCapabilityView:
    """Return a runtime capability view for an entry, coordinator, catalog, or view."""
    if isinstance(source, RuntimeCapabilityView):
        return source

    runtime_data = getattr(source, "runtime_data", None)
    if runtime_data is not None:
        return runtime_model_view(getattr(runtime_data, "coordinator", None))

    runtime_state = getattr(source, "runtime_state", None)
    if runtime_state is not None:
        state_view = getattr(runtime_state, "model_view", None)
        if isinstance(state_view, RuntimeCapabilityView):
            return state_view

    view = getattr(source, "model_view", None)
    if isinstance(view, RuntimeCapabilityView):
        return view

    if isinstance(source, LemonadeModelCatalog):
        return RuntimeCapabilityView(source)

    catalog = getattr(source, "catalog", None)
    if isinstance(catalog, LemonadeModelCatalog):
        return RuntimeCapabilityView(catalog)

    raise TypeError(f"Invalid Lemonade runtime model source: {type(source).__name__}")


def default_model_selector_definition(
    option_key: str | None,
) -> DefaultModelSelectorDefinition | None:
    """Return the Server Entry Model Selector policy for an option key."""
    return next(
        (
            definition
            for definition in default_model_selector_definitions()
            if definition.option_key == option_key
        ),
        None,
    )


def default_model_capability_presentations() -> Iterable[CapabilityPresentation]:
    """Iterate capabilities configurable as default model options."""
    return (
        description.to_presentation()
        for description in CAPABILITY_DESCRIPTIONS
        if description.default_option_key is not None
    )


def default_model_selector_definitions() -> Iterable[DefaultModelSelectorDefinition]:
    """Iterate Server Entry default Model Selector definitions."""
    return (
        DefaultModelSelectorDefinition(
            description.capability,
            description.default_option_key,
            description.selector_name,
            description.degraded_policy,
        )
        for description in CAPABILITY_DESCRIPTIONS
        if description.default_option_key is not None
    )


def model_count_sensor_policies() -> Iterable[ModelCountSensorPolicy]:
    """Iterate Server Entry model-count sensor policies."""
    return (
        ModelCountSensorPolicy(
            description.capability,
            description.model_count_translation_key,
        )
        for description in CAPABILITY_DESCRIPTIONS
        if description.model_count_translation_key is not None
    )


def model_count_capability_presentations() -> Iterable[CapabilityPresentation]:
    """Iterate capabilities shown as model count sensors."""
    return (
        description.to_presentation()
        for description in CAPABILITY_DESCRIPTIONS
        if description.model_count_translation_key is not None
    )


def repair_issue_identities() -> Iterable[MissingCapabilityRepairIssueIdentity]:
    """Iterate missing-capability repair issue identities."""
    return (
        MissingCapabilityRepairIssueIdentity(description.capability)
        for description in CAPABILITY_DESCRIPTIONS
        if description.repair_issue
    )


def repair_issue_capabilities() -> Iterable[Capability]:
    """Iterate legacy missing-capability repair issues to clean up."""
    return (identity.capability for identity in repair_issue_identities())
