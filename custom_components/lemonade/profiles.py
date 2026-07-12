"""Shared runtime helpers for Lemonade profile subentries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
import inspect
from types import MappingProxyType
from typing import Any, Protocol, TypeAlias, assert_never

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


class ProfileField(Protocol):
    """Small interface shared by well-formed profile field definitions."""

    @property
    def key(self) -> str:
        """Return the persisted profile-data key."""
        ...


@dataclass(frozen=True, slots=True)
class TextProfileField:
    """Required or optional plain-text profile field."""

    key: str
    required: bool = False


@dataclass(frozen=True, slots=True)
class ModelProfileField:
    """Optional Lemonade model profile field."""

    key: str


@dataclass(frozen=True, slots=True)
class NumberProfileField:
    """Optional integral profile field with a lower bound."""

    key: str
    minimum: int
    default: int | None = None


@dataclass(frozen=True, slots=True)
class PromptProfileField:
    """Optional template prompt profile field."""

    key: str
    suggest_default_instructions: bool = False


@dataclass(frozen=True, slots=True)
class LLMAPIProfileField:
    """Optional Home Assistant LLM API profile field."""

    key: str

ProfileFieldDefinition: TypeAlias = (
    TextProfileField
    | ModelProfileField
    | NumberProfileField
    | PromptProfileField
    | LLMAPIProfileField
)


class ProfileFieldPresentation(StrEnum):
    """Adapter-neutral presentation treatments for profile fields."""

    TEXT = "text"
    MODEL = "model"
    PROMPT = "prompt"
    LLM_API = "llm_api"
    NUMBER = "number"


class _ProfileFieldParser(StrEnum):
    """Closed persisted-value normalization treatments."""

    OPTIONAL_STRING = "optional_string"
    MODEL_ID = "model_id"
    INTEGER = "integer"


@dataclass(frozen=True, slots=True)
class ProfileFieldInterpretation:
    """Complete adapter-neutral meaning of one profile field definition."""

    key: str
    required: bool
    presentation: ProfileFieldPresentation
    parser: _ProfileFieldParser
    default: int | None = None
    minimum: int | None = None
    suggest_default_instructions: bool = False


def interpret_profile_field(
    field: ProfileFieldDefinition,
) -> ProfileFieldInterpretation:
    """Exhaustively project a closed field case into its complete semantics."""
    match field:
        case TextProfileField(key=key, required=required):
            return ProfileFieldInterpretation(
                key, required, ProfileFieldPresentation.TEXT,
                _ProfileFieldParser.OPTIONAL_STRING,
            )
        case ModelProfileField(key=key):
            return ProfileFieldInterpretation(
                key, False, ProfileFieldPresentation.MODEL,
                _ProfileFieldParser.MODEL_ID,
            )
        case NumberProfileField(key=key, minimum=minimum, default=default):
            return ProfileFieldInterpretation(
                key, False, ProfileFieldPresentation.NUMBER,
                _ProfileFieldParser.INTEGER, default, minimum,
            )
        case PromptProfileField(
            key=key,
            suggest_default_instructions=suggest_default_instructions,
        ):
            return ProfileFieldInterpretation(
                key, False, ProfileFieldPresentation.PROMPT,
                _ProfileFieldParser.OPTIONAL_STRING,
                suggest_default_instructions=suggest_default_instructions,
            )
        case LLMAPIProfileField(key=key):
            return ProfileFieldInterpretation(
                key, False, ProfileFieldPresentation.LLM_API,
                _ProfileFieldParser.OPTIONAL_STRING,
            )
        case _:
            assert_never(field)


def normalize_profile_field(field: ProfileFieldDefinition, value: Any) -> Any:
    """Normalize one persisted value according to interpreted field meaning."""
    interpretation = interpret_profile_field(field)
    if interpretation.parser is _ProfileFieldParser.OPTIONAL_STRING:
        return _optional_str(value)
    if interpretation.parser is _ProfileFieldParser.MODEL_ID:
        model_id = ModelId.parse(value)
        return str(model_id) if model_id is not None else None
    if interpretation.parser is _ProfileFieldParser.INTEGER:
        if value is None:
            return interpretation.default
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return interpretation.default
        minimum = interpretation.minimum
        if minimum is not None and normalized < minimum:
            return minimum if interpretation.default is not None else None
        return normalized
    assert_never(interpretation.parser)


def normalize_profile_data(
    definition: ProfileDefinition,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize all supported persisted values for a profile definition."""
    return {
        field.key: normalize_profile_field(field, data.get(field.key))
        for field in definition.fields
    }


@dataclass(frozen=True, slots=True)
class ProfileDefinition:
    """Definition for a Lemonade profile subentry type."""

    profile_type: ProfileKind
    capability: Capability
    fields: tuple[ProfileFieldDefinition, ...]
    model_policy: ProfileModelPolicy

    @property
    def supported_fields(self) -> tuple[str, ...]:
        """Return supported profile field keys."""
        return tuple(field.key for field in self.fields)


CONVERSATION_PROFILE_DEFINITION = ProfileDefinition(
    profile_type=ProfileKind.CONVERSATION,
    capability=Capability.CONVERSATION,
    fields=(
        TextProfileField(CONF_NAME, required=True),
        ModelProfileField(CONF_MODEL),
        PromptProfileField(CONF_PROMPT, suggest_default_instructions=True),
        LLMAPIProfileField(CONF_LLM_HASS_API),
        NumberProfileField(CONF_MAX_HISTORY, minimum=0, default=DEFAULT_MAX_HISTORY),
        NumberProfileField(CONF_KEEP_ALIVE, minimum=-1),
    ),
    model_policy=ProfileModelPolicy(Capability.CONVERSATION),
)
AI_TASK_PROFILE_DEFINITION = ProfileDefinition(
    profile_type=ProfileKind.AI_TASK,
    capability=Capability.AI_TASK,
    fields=(
        TextProfileField(CONF_NAME, required=True),
        ModelProfileField(CONF_MODEL),
        PromptProfileField(CONF_PROMPT),
        NumberProfileField(CONF_MAX_HISTORY, minimum=0, default=DEFAULT_MAX_HISTORY),
        NumberProfileField(CONF_KEEP_ALIVE, minimum=-1),
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
        normalized = normalize_profile_data(definition, data)
        return ConversationProfile(
            id=profile_id,
            profile_type=definition.profile_type,
            model=normalized[CONF_MODEL],
            prompt=normalized[CONF_PROMPT],
            hass_api=normalized[CONF_LLM_HASS_API],
            max_history=normalized[CONF_MAX_HISTORY],
            keep_alive=normalized[CONF_KEEP_ALIVE],
        )
    if definition == AI_TASK_PROFILE_DEFINITION:
        normalized = normalize_profile_data(definition, data)
        return AITaskProfile(
            id=profile_id,
            profile_type=definition.profile_type,
            model=normalized[CONF_MODEL],
            prompt=normalized[CONF_PROMPT],
            max_history=normalized[CONF_MAX_HISTORY],
            keep_alive=normalized[CONF_KEEP_ALIVE],
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
