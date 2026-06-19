"""Shared runtime helpers for Lemonade profile subentries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import inspect
from types import MappingProxyType
from typing import Any

from homeassistant.const import CONF_MODEL
try:
    from homeassistant.const import CONF_PROMPT
except ImportError:  # pragma: no cover - older Home Assistant compatibility
    CONF_PROMPT = "prompt"

from .const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CONF_LLM_HASS_API,
    SUBENTRY_TYPE_AI_TASK,
    SUBENTRY_TYPE_CONVERSATION,
)


@dataclass(frozen=True, slots=True)
class ConversationProfile:
    """Parsed conversation profile subentry data."""

    id: str | None
    profile_type: str
    model: Any = None
    prompt: Any = None
    hass_api: Any = None


@dataclass(frozen=True, slots=True)
class AITaskProfile:
    """Parsed AI task profile subentry data."""

    id: str | None
    profile_type: str
    model: Any = None
    prompt: Any = None


@dataclass(frozen=True, slots=True)
class UnknownProfile:
    """Parsed profile wrapper for unsupported subentry types."""

    id: str | None
    profile_type: str | None
    data: Mapping[str, Any]


Profile = ConversationProfile | AITaskProfile | UnknownProfile


PROFILE_CAPABILITY_BY_SUBENTRY_TYPE = MappingProxyType(
    {
        SUBENTRY_TYPE_CONVERSATION: CAPABILITY_CONVERSATION,
        SUBENTRY_TYPE_AI_TASK: CAPABILITY_AI_TASK,
    }
)


def profile_capability(profile_type: str) -> str | None:
    """Return the model capability required by a Lemonade profile type."""
    return PROFILE_CAPABILITY_BY_SUBENTRY_TYPE.get(profile_type)


def profile_data(subentry: Any) -> dict[str, Any]:
    """Return profile subentry data as a plain dict."""
    data = getattr(subentry, "data", {}) or {}
    if isinstance(data, Mapping):
        return dict(data)
    return {}


def parse_profile(subentry: Any, profile_type: str | None = None) -> Profile:
    """Parse a Home Assistant profile subentry into a typed profile record."""
    data = profile_data(subentry)
    resolved_profile_type = profile_type or getattr(subentry, "subentry_type", None)
    profile_id = getattr(subentry, "subentry_id", None)
    if resolved_profile_type == SUBENTRY_TYPE_CONVERSATION:
        return ConversationProfile(
            id=profile_id,
            profile_type=SUBENTRY_TYPE_CONVERSATION,
            model=data.get(CONF_MODEL),
            prompt=data.get(CONF_PROMPT),
            hass_api=data.get(CONF_LLM_HASS_API),
        )
    if resolved_profile_type == SUBENTRY_TYPE_AI_TASK:
        return AITaskProfile(
            id=profile_id,
            profile_type=SUBENTRY_TYPE_AI_TASK,
            model=data.get(CONF_MODEL),
            prompt=data.get(CONF_PROMPT),
        )
    return UnknownProfile(
        id=profile_id,
        profile_type=resolved_profile_type,
        data=MappingProxyType(data),
    )


def profile_subentries(entry: Any, profile_type: str) -> list[Any]:
    """Return profile subentries of a specific type from a config entry."""
    subentries = getattr(entry, "subentries", {}) or {}
    values = subentries.values() if isinstance(subentries, Mapping) else subentries
    return [
        subentry
        for subentry in values
        if getattr(subentry, "subentry_type", None) == profile_type
    ]


async def _maybe_await(value: Any) -> Any:
    """Await a value only when it is awaitable."""
    if inspect.isawaitable(value):
        return await value
    return value


async def async_add_profile_entity(
    async_add_entities: Callable[..., Any],
    entity: Any,
    config_subentry_id: str | None,
) -> None:
    """Add a profile entity with config subentry ID compatibility fallback."""
    if config_subentry_id is None:
        await _maybe_await(async_add_entities([entity]))
        return

    try:
        result = async_add_entities([entity], config_subentry_id=config_subentry_id)
    except TypeError:
        result = async_add_entities([entity])
    await _maybe_await(result)
