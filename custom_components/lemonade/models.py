"""Model catalog parsing for Lemonade Server."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .const import (
    CAPABILITIES,
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CAPABILITY_EMBEDDINGS,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_STT,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_TTS,
    CAPABILITY_VISION,
)

EXCLUDED_LLM_LABELS = {"image", "tts", "embeddings"}
TOOL_CALLING_LABELS = {"tool-calling", "tool_calling"}
STT_LABELS = {"stt", "transcription", "speech-to-text"}


class Capability(StrEnum):
    """Closed Lemonade model capability values."""

    CONVERSATION = CAPABILITY_CONVERSATION
    AI_TASK = CAPABILITY_AI_TASK
    TOOL_CALLING = CAPABILITY_TOOL_CALLING
    VISION = CAPABILITY_VISION
    IMAGE = CAPABILITY_IMAGE
    IMAGE_EDIT = CAPABILITY_IMAGE_EDIT
    TTS = CAPABILITY_TTS
    STT = CAPABILITY_STT
    EMBEDDINGS = CAPABILITY_EMBEDDINGS

    @classmethod
    def parse(cls, value: Any) -> "Capability | None":
        """Return a capability for known external values."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls(value)
            except ValueError:
                return None
        return None


CAPABILITY_ORDER = tuple(Capability(capability) for capability in CAPABILITIES)


@dataclass(frozen=True)
class ModelId:
    """Validated Lemonade model ID."""

    value: str

    def __post_init__(self) -> None:
        """Normalize and reject blank model IDs."""
        if not isinstance(self.value, str):
            raise TypeError("Model ID must be a string")
        value = self.value.strip()
        if not value:
            raise ValueError("Model ID must not be blank")
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        """Return the Home Assistant-facing model ID string."""
        return self.value

    @classmethod
    def parse(cls, value: Any) -> "ModelId | None":
        """Return a model ID for valid external values."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            return None
        value = value.strip()
        if not value:
            return None
        return cls(value)


@dataclass(frozen=True)
class LemonadeModel:
    """A Lemonade model returned by the models endpoint."""

    id: ModelId
    labels: frozenset[str]
    recipe: str
    downloaded: bool
    raw: Mapping[str, Any]

    @property
    def is_llm(self) -> bool:
        """Return true when the model is a general Llama.cpp LLM."""
        return self.recipe == "llamacpp" and not (self.labels & EXCLUDED_LLM_LABELS)


@dataclass(frozen=True)
class LemonadeModelCatalog:
    """Parsed Lemonade models grouped by capability."""

    models: tuple[LemonadeModel, ...]
    by_capability: Mapping[Capability, tuple[LemonadeModel, ...]]

    @property
    def all_model_ids(self) -> list[str]:
        """Return every parsed model ID."""
        return [str(model.id) for model in self.models]

    def models_for(self, capability: Capability | str) -> tuple[LemonadeModel, ...]:
        """Return models for a capability."""
        parsed_capability = Capability.parse(capability)
        if parsed_capability is None:
            return ()
        return self.by_capability.get(parsed_capability, ())

    def model_ids(self, capability: Capability | str) -> list[str]:
        """Return model IDs for a capability."""
        return [str(model.id) for model in self.models_for(capability)]

    def first_model_id(self, capability: Capability | str) -> str | None:
        """Return the first model ID for a capability, if any."""
        models = self.models_for(capability)
        return str(models[0].id) if models else None


def _raw_models(response: Any) -> Iterable[Any]:
    """Return raw model records from a Lemonade models response."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        for key in ("data", "models"):
            models = response.get(key)
            if isinstance(models, list):
                return models
    return ()


def _labels(raw: Mapping[str, Any]) -> frozenset[str]:
    """Return normalized labels for a raw model."""
    labels = raw.get("labels", ())
    if isinstance(labels, str):
        return frozenset({labels.strip().lower()} if labels.strip() else ())
    if isinstance(labels, Iterable):
        return frozenset(
            label.strip().lower()
            for label in labels
            if isinstance(label, str) and label.strip()
        )
    return frozenset()


def _recipe(raw: Mapping[str, Any]) -> str:
    """Return the normalized recipe for a raw model."""
    recipe = raw.get("recipe", "")
    return recipe.strip().lower() if isinstance(recipe, str) else ""


def _capabilities(model: LemonadeModel) -> tuple[Capability, ...]:
    """Return capabilities exposed by a parsed model."""
    capabilities: list[Capability] = []

    if model.is_llm:
        capabilities.extend(
            (
                Capability.CONVERSATION,
                Capability.AI_TASK,
            )
        )

    if model.labels & TOOL_CALLING_LABELS:
        capabilities.append(Capability.TOOL_CALLING)

    if CAPABILITY_VISION in model.labels:
        capabilities.append(Capability.VISION)
    if CAPABILITY_IMAGE in model.labels:
        capabilities.append(Capability.IMAGE)
    if model.labels & {CAPABILITY_IMAGE_EDIT, "image-edit", "edit"}:
        capabilities.append(Capability.IMAGE_EDIT)
    if CAPABILITY_TTS in model.labels:
        capabilities.append(Capability.TTS)
    if model.labels & STT_LABELS:
        capabilities.append(Capability.STT)
    if CAPABILITY_EMBEDDINGS in model.labels:
        capabilities.append(Capability.EMBEDDINGS)

    return tuple(
        capability for capability in CAPABILITY_ORDER if capability in capabilities
    )


def parse_models_response(response: Any) -> LemonadeModelCatalog:
    """Parse a Lemonade models response into a capability catalog."""
    models: list[LemonadeModel] = []
    by_capability: dict[Capability, list[LemonadeModel]] = {
        capability: [] for capability in CAPABILITY_ORDER
    }

    for raw in _raw_models(response):
        if not isinstance(raw, Mapping):
            continue

        model_id = ModelId.parse(raw.get("id"))
        if model_id is None:
            continue

        downloaded = raw.get("downloaded", True)
        if downloaded is False:
            continue

        model = LemonadeModel(
            id=model_id,
            labels=_labels(raw),
            recipe=_recipe(raw),
            downloaded=True,
            raw=raw,
        )
        models.append(model)

        for capability in _capabilities(model):
            by_capability[capability].append(model)

    return LemonadeModelCatalog(
        models=tuple(models),
        by_capability={
            capability: tuple(capability_models)
            for capability, capability_models in by_capability.items()
        },
    )
