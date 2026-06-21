"""Shared runtime helpers for Lemonade profile subentries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
import inspect
from types import MappingProxyType
from typing import Any

from homeassistant.const import CONF_MODEL, CONF_NAME
try:
    from homeassistant.const import CONF_PROMPT
except ImportError:  # pragma: no cover - older Home Assistant compatibility
    CONF_PROMPT = "prompt"

from .const import (
    CONF_KEEP_ALIVE,
    CONF_LLM_HASS_API,
    CONF_MAX_HISTORY,
    DEFAULT_MAX_HISTORY,
    SUBENTRY_TYPE_AI_TASK,
    SUBENTRY_TYPE_CONVERSATION,
)
from .models import Capability, ModelId


class ProfileKind(StrEnum):
    """Closed Lemonade profile subentry types."""

    CONVERSATION = SUBENTRY_TYPE_CONVERSATION
    AI_TASK = SUBENTRY_TYPE_AI_TASK

    @classmethod
    def parse(cls, value: Any) -> "ProfileKind | None":
        """Return a profile kind for known external values."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls(value)
            except ValueError:
                return None
        return None


class ProfileFieldSelectorKind(StrEnum):
    """Closed Home Assistant selector kinds for profile fields."""

    STRING = "string"
    MODEL = "model"
    TEMPLATE = "template"
    LLM_API = "llm_api"
    NUMBER = "number"


class ProfilePromptPolicy(StrEnum):
    """Closed prompt default behavior for profile fields."""

    NONE = "none"
    DEFAULT_INSTRUCTIONS = "default_instructions"


@dataclass(frozen=True, slots=True)
class ConversationProfile:
    """Parsed conversation profile subentry data."""

    id: str | None
    profile_type: ProfileKind
    model: str | None = None
    prompt: str | None = None
    hass_api: str | None = None
    max_history: int = DEFAULT_MAX_HISTORY
    keep_alive: int | None = None


@dataclass(frozen=True, slots=True)
class AITaskProfile:
    """Parsed AI task profile subentry data."""

    id: str | None
    profile_type: ProfileKind
    model: str | None = None
    prompt: str | None = None
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
class ProfileModelPolicy:
    """Model selection policy for a Lemonade profile setup."""

    capability: Capability
    include_all_models: bool = True


@dataclass(frozen=True, slots=True)
class ProfileFieldDefinition:
    """Definition for a Lemonade profile setup field."""

    key: str
    selector_kind: ProfileFieldSelectorKind
    required: bool = False
    default: Any = None
    prompt_policy: ProfilePromptPolicy = ProfilePromptPolicy.NONE
    minimum: int | None = None

    def default_value(self, profile_data: Mapping[str, Any]) -> Any:
        """Return this field's persisted or definition default."""
        if self.key in profile_data:
            return profile_data[self.key]
        return self.default

    def prompt_suggested_value(
        self,
        profile_data: Mapping[str, Any],
        default_instructions_prompt: str | None,
    ) -> str | None:
        """Return a suggested prompt value when this field policy allows it."""
        if self.key in profile_data:
            return None
        if self.prompt_policy != ProfilePromptPolicy.DEFAULT_INSTRUCTIONS:
            return None
        return default_instructions_prompt


@dataclass(frozen=True, slots=True)
class ProfileDefinition:
    """Definition for a Lemonade profile subentry type."""

    profile_type: ProfileKind
    capability: Capability
    fields: tuple[ProfileFieldDefinition, ...]
    model_policy: ProfileModelPolicy
    llm_hass_api_field: str | None = None

    @property
    def supported_fields(self) -> tuple[str, ...]:
        """Return supported profile field keys."""
        return tuple(field.key for field in self.fields)


CONVERSATION_PROFILE_DEFINITION = ProfileDefinition(
    profile_type=ProfileKind.CONVERSATION,
    capability=Capability.CONVERSATION,
    fields=(
        ProfileFieldDefinition(
            CONF_NAME,
            ProfileFieldSelectorKind.STRING,
            required=True,
        ),
        ProfileFieldDefinition(CONF_MODEL, ProfileFieldSelectorKind.MODEL),
        ProfileFieldDefinition(
            CONF_PROMPT,
            ProfileFieldSelectorKind.TEMPLATE,
            prompt_policy=ProfilePromptPolicy.DEFAULT_INSTRUCTIONS,
        ),
        ProfileFieldDefinition(CONF_LLM_HASS_API, ProfileFieldSelectorKind.LLM_API),
        ProfileFieldDefinition(
            CONF_MAX_HISTORY,
            ProfileFieldSelectorKind.NUMBER,
            default=DEFAULT_MAX_HISTORY,
            minimum=0,
        ),
        ProfileFieldDefinition(
            CONF_KEEP_ALIVE,
            ProfileFieldSelectorKind.NUMBER,
            minimum=-1,
        ),
    ),
    model_policy=ProfileModelPolicy(Capability.CONVERSATION),
    llm_hass_api_field=CONF_LLM_HASS_API,
)
AI_TASK_PROFILE_DEFINITION = ProfileDefinition(
    profile_type=ProfileKind.AI_TASK,
    capability=Capability.AI_TASK,
    fields=(
        ProfileFieldDefinition(
            CONF_NAME,
            ProfileFieldSelectorKind.STRING,
            required=True,
        ),
        ProfileFieldDefinition(CONF_MODEL, ProfileFieldSelectorKind.MODEL),
        ProfileFieldDefinition(CONF_PROMPT, ProfileFieldSelectorKind.TEMPLATE),
        ProfileFieldDefinition(
            CONF_MAX_HISTORY,
            ProfileFieldSelectorKind.NUMBER,
            default=DEFAULT_MAX_HISTORY,
            minimum=0,
        ),
        ProfileFieldDefinition(
            CONF_KEEP_ALIVE,
            ProfileFieldSelectorKind.NUMBER,
            minimum=-1,
        ),
    ),
    model_policy=ProfileModelPolicy(Capability.AI_TASK),
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


def profile_definition(
    profile_type: ProfileKind | str | None,
) -> ProfileDefinition | None:
    """Return the definition for a Lemonade profile type."""
    kind = ProfileKind.parse(profile_type)
    if kind is None:
        return None
    return PROFILE_DEFINITION_BY_TYPE.get(kind)


def profile_capability(profile_type: ProfileKind | str) -> Capability | None:
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


def _optional_str(value: Any) -> str | None:
    """Return a stripped non-empty string option."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _profile_id(value: Any) -> str | None:
    """Return a normalized profile subentry ID."""
    return _optional_str(value)


def _model_option(data: Mapping[str, Any]) -> str | None:
    """Return a normalized optional Lemonade model ID."""
    model_id = ModelId.parse(data.get(CONF_MODEL))
    return str(model_id) if model_id is not None else None


def _prompt_option(data: Mapping[str, Any]) -> str | None:
    """Return a normalized optional profile prompt."""
    return _optional_str(data.get(CONF_PROMPT))


def _llm_hass_api_option(data: Mapping[str, Any], key: str | None) -> str | None:
    """Return a normalized optional Home Assistant LLM API ID."""
    if key is None:
        return None
    return _optional_str(data.get(key))


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


def _keep_alive_option(data: Mapping[str, Any]) -> int | None:
    """Return a normalized optional keep-alive override."""
    value = _int_profile_option(data, CONF_KEEP_ALIVE)
    if value is None or value < -1:
        return None
    return value


def parse_profile(
    subentry: Any,
    profile_type: ProfileKind | str | None = None,
) -> Profile:
    """Parse a Home Assistant profile subentry into a typed profile record."""
    data = profile_data(subentry)
    resolved_profile_type = profile_type or getattr(subentry, "subentry_type", None)
    profile_id = _profile_id(getattr(subentry, "subentry_id", None))
    definition = profile_definition(resolved_profile_type)
    if definition == CONVERSATION_PROFILE_DEFINITION:
        return ConversationProfile(
            id=profile_id,
            profile_type=definition.profile_type,
            model=_model_option(data),
            prompt=_prompt_option(data),
            hass_api=_llm_hass_api_option(data, definition.llm_hass_api_field),
            max_history=_max_history_option(data),
            keep_alive=_keep_alive_option(data),
        )
    if definition == AI_TASK_PROFILE_DEFINITION:
        return AITaskProfile(
            id=profile_id,
            profile_type=definition.profile_type,
            model=_model_option(data),
            prompt=_prompt_option(data),
            max_history=_max_history_option(data),
            keep_alive=_keep_alive_option(data),
        )
    return UnknownProfile(
        id=profile_id,
        profile_type=resolved_profile_type,
        data=MappingProxyType(data),
    )


def parse_conversation_profile(subentry: Any) -> ConversationProfile:
    """Parse a Home Assistant subentry into a conversation profile."""
    profile = parse_profile(subentry, ProfileKind.CONVERSATION)
    if isinstance(profile, ConversationProfile):
        return profile
    raise TypeError("Expected a conversation profile subentry")


def parse_ai_task_profile(subentry: Any) -> AITaskProfile:
    """Parse a Home Assistant subentry into an AI task profile."""
    profile = parse_profile(subentry, ProfileKind.AI_TASK)
    if isinstance(profile, AITaskProfile):
        return profile
    raise TypeError("Expected an AI task profile subentry")


def profile_subentries(entry: Any, profile_type: ProfileKind | str) -> list[Any]:
    """Return profile subentries of a specific type from a config entry."""
    kind = ProfileKind.parse(profile_type)
    if kind is None:
        return []
    subentries = getattr(entry, "subentries", {}) or {}
    values = subentries.values() if isinstance(subentries, Mapping) else subentries
    return [
        subentry
        for subentry in values
        if ProfileKind.parse(getattr(subentry, "subentry_type", None)) == kind
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
