"""Shared runtime helpers for Lemonade profile subentries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import inspect
from types import MappingProxyType
from typing import Any

from homeassistant.const import CONF_MODEL, CONF_NAME
try:
    from homeassistant.const import CONF_PROMPT
except ImportError:  # pragma: no cover - older Home Assistant compatibility
    CONF_PROMPT = "prompt"

from .const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CONF_KEEP_ALIVE,
    CONF_LLM_HASS_API,
    CONF_MAX_HISTORY,
    DEFAULT_MAX_HISTORY,
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
    max_history: int = DEFAULT_MAX_HISTORY
    keep_alive: int | None = None


@dataclass(frozen=True, slots=True)
class AITaskProfile:
    """Parsed AI task profile subentry data."""

    id: str | None
    profile_type: str
    model: Any = None
    prompt: Any = None
    max_history: int = DEFAULT_MAX_HISTORY
    keep_alive: int | None = None


@dataclass(frozen=True, slots=True)
class UnknownProfile:
    """Parsed profile wrapper for unsupported subentry types."""

    id: str | None
    profile_type: str | None
    data: Mapping[str, Any]


Profile = ConversationProfile | AITaskProfile | UnknownProfile


@dataclass(frozen=True, slots=True)
class ProfileDefinition:
    """Definition for a Lemonade profile subentry type."""

    profile_type: str
    capability: str
    supported_fields: tuple[str, ...]
    llm_hass_api_field: str | None = None


CONVERSATION_PROFILE_DEFINITION = ProfileDefinition(
    profile_type=SUBENTRY_TYPE_CONVERSATION,
    capability=CAPABILITY_CONVERSATION,
    supported_fields=(
        CONF_NAME,
        CONF_MODEL,
        CONF_PROMPT,
        CONF_LLM_HASS_API,
        CONF_MAX_HISTORY,
        CONF_KEEP_ALIVE,
    ),
    llm_hass_api_field=CONF_LLM_HASS_API,
)
AI_TASK_PROFILE_DEFINITION = ProfileDefinition(
    profile_type=SUBENTRY_TYPE_AI_TASK,
    capability=CAPABILITY_AI_TASK,
    supported_fields=(
        CONF_NAME,
        CONF_MODEL,
        CONF_PROMPT,
        CONF_MAX_HISTORY,
        CONF_KEEP_ALIVE,
    ),
)
PROFILE_DEFINITIONS = (
    CONVERSATION_PROFILE_DEFINITION,
    AI_TASK_PROFILE_DEFINITION,
)
PROFILE_DEFINITION_BY_TYPE = MappingProxyType(
    {definition.profile_type: definition for definition in PROFILE_DEFINITIONS}
)


def profile_definitions() -> tuple[ProfileDefinition, ...]:
    """Return supported Lemonade profile definitions."""
    return PROFILE_DEFINITIONS


def profile_definition(profile_type: str | None) -> ProfileDefinition | None:
    """Return the definition for a Lemonade profile type."""
    return PROFILE_DEFINITION_BY_TYPE.get(profile_type)


def profile_capability(profile_type: str) -> str | None:
    """Return the model capability required by a Lemonade profile type."""
    definition = profile_definition(profile_type)
    return definition.capability if definition is not None else None


def profile_data(subentry: Any) -> dict[str, Any]:
    """Return profile subentry data as a plain dict."""
    data = getattr(subentry, "data", {}) or {}
    if isinstance(data, Mapping):
        return dict(data)
    return {}


def profile_title(subentry: Any, fallback: str | None = None) -> str | None:
    """Return the user-facing title for a profile subentry."""
    return (
        getattr(subentry, "title", None)
        or profile_data(subentry).get(CONF_NAME)
        or fallback
    )


def _int_profile_option(
    data: Mapping[str, Any],
    key: str,
    default: int | None = None,
) -> int | None:
    """Return an optional integer profile option."""
    value = data.get(key, default)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _max_history_option(data: Mapping[str, Any]) -> int:
    """Return the profile history limit."""
    value = _int_profile_option(data, CONF_MAX_HISTORY, DEFAULT_MAX_HISTORY)
    if value is None:
        return DEFAULT_MAX_HISTORY
    return max(0, value)


def parse_profile(subentry: Any, profile_type: str | None = None) -> Profile:
    """Parse a Home Assistant profile subentry into a typed profile record."""
    data = profile_data(subentry)
    resolved_profile_type = profile_type or getattr(subentry, "subentry_type", None)
    profile_id = getattr(subentry, "subentry_id", None)
    definition = profile_definition(resolved_profile_type)
    if definition == CONVERSATION_PROFILE_DEFINITION:
        return ConversationProfile(
            id=profile_id,
            profile_type=definition.profile_type,
            model=data.get(CONF_MODEL),
            prompt=data.get(CONF_PROMPT),
            hass_api=data.get(definition.llm_hass_api_field),
            max_history=_max_history_option(data),
            keep_alive=_int_profile_option(data, CONF_KEEP_ALIVE),
        )
    if definition == AI_TASK_PROFILE_DEFINITION:
        return AITaskProfile(
            id=profile_id,
            profile_type=definition.profile_type,
            model=data.get(CONF_MODEL),
            prompt=data.get(CONF_PROMPT),
            max_history=_max_history_option(data),
            keep_alive=_int_profile_option(data, CONF_KEEP_ALIVE),
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
