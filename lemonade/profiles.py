"""Shared runtime helpers for Lemonade profile subentries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import inspect
from types import MappingProxyType
from typing import Any

from .const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    SUBENTRY_TYPE_AI_TASK,
    SUBENTRY_TYPE_CONVERSATION,
)

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
