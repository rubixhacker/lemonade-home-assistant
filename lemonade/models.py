"""Model catalog parsing for Lemonade Server."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
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
STT_LABELS = {"stt", "transcription", "speech-to-text"}


@dataclass(frozen=True)
class LemonadeModel:
    """A Lemonade model returned by the models endpoint."""

    id: str
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
    by_capability: Mapping[str, tuple[LemonadeModel, ...]]

    @property
    def all_model_ids(self) -> list[str]:
        """Return every parsed model ID."""
        return [model.id for model in self.models]

    def models_for(self, capability: str) -> tuple[LemonadeModel, ...]:
        """Return models for a capability."""
        return self.by_capability.get(capability, ())

    def model_ids(self, capability: str) -> list[str]:
        """Return model IDs for a capability."""
        return [model.id for model in self.models_for(capability)]

    def first_model_id(self, capability: str) -> str | None:
        """Return the first model ID for a capability, if any."""
        models = self.by_capability.get(capability, ())
        return models[0].id if models else None


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


def _capabilities(model: LemonadeModel) -> tuple[str, ...]:
    """Return capabilities exposed by a parsed model."""
    capabilities: list[str] = []

    if model.is_llm:
        capabilities.extend(
            (
                CAPABILITY_CONVERSATION,
                CAPABILITY_AI_TASK,
            )
        )

    if "tool-calling" in model.labels:
        capabilities.append(CAPABILITY_TOOL_CALLING)

    if CAPABILITY_VISION in model.labels:
        capabilities.append(CAPABILITY_VISION)
    if CAPABILITY_IMAGE in model.labels:
        capabilities.append(CAPABILITY_IMAGE)
    if model.labels & {CAPABILITY_IMAGE_EDIT, "image-edit", "edit"}:
        capabilities.append(CAPABILITY_IMAGE_EDIT)
    if CAPABILITY_TTS in model.labels:
        capabilities.append(CAPABILITY_TTS)
    if model.labels & STT_LABELS:
        capabilities.append(CAPABILITY_STT)
    if CAPABILITY_EMBEDDINGS in model.labels:
        capabilities.append(CAPABILITY_EMBEDDINGS)

    return tuple(capability for capability in CAPABILITIES if capability in capabilities)


def parse_models_response(response: Any) -> LemonadeModelCatalog:
    """Parse a Lemonade models response into a capability catalog."""
    models: list[LemonadeModel] = []
    by_capability: dict[str, list[LemonadeModel]] = {
        capability: [] for capability in CAPABILITIES
    }

    for raw in _raw_models(response):
        if not isinstance(raw, Mapping):
            continue

        model_id = raw.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue

        downloaded = raw.get("downloaded", True)
        if downloaded is False:
            continue

        model = LemonadeModel(
            id=model_id.strip(),
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
