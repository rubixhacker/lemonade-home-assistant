"""Profile-level Lemonade chat turn orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from homeassistant.components.conversation import SystemContent
except ImportError:  # pragma: no cover - compatibility with HA module layouts
    from homeassistant.components.conversation.models import SystemContent  # type: ignore[no-redef]
from homeassistant.exceptions import HomeAssistantError

from .const import CAPABILITY_AI_TASK, CAPABILITY_CONVERSATION, DOMAIN
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .llm import (
    async_execute_chat_log_turn,
    async_generate_chat_log_data,
)
from .model_resolution import resolve_entry_model
from .profiles import AITaskProfile, ConversationProfile


@dataclass(frozen=True, slots=True)
class ProfileChatTurn:
    """Resolved Lemonade profile chat turn invocation."""

    entity_id: str
    client: Any
    model: str
    chat_log: Any
    structure: Any | None = None
    prompt: str | None = None
    max_history: int | None = None
    keep_alive: int | None = None


class ProfilePromptedChatLog:
    """ChatLog proxy that prepends a system prompt without mutating the source."""

    def __init__(self, chat_log: Any, prompt: str) -> None:
        self._chat_log = chat_log
        self._system_content = SystemContent(prompt)

    @property
    def content(self) -> list[Any]:
        """Return current chat content with the injected system prompt first."""
        content = getattr(self._chat_log, "content", [])
        return [self._system_content, *list(content or [])]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat_log, name)


def resolve_conversation_profile_model(entry: Any, profile: ConversationProfile) -> str:
    """Return the model configured for a conversation profile chat turn."""
    model = resolve_entry_model(
        entry,
        CAPABILITY_CONVERSATION,
        profile_model=profile.model,
    )
    if model is not None:
        return model

    raise HomeAssistantError("No Lemonade conversation model is available")


def resolve_ai_task_profile_model(entry: Any, profile: AITaskProfile) -> str:
    """Return the model configured for an AI task profile data chat turn."""
    model = resolve_entry_model(
        entry,
        CAPABILITY_AI_TASK,
        profile_model=profile.model,
    )
    if model is not None:
        return model

    raise HomeAssistantError("No Lemonade AI task model is available")


def chat_log_with_profile_prompt(chat_log: Any, prompt: str | None) -> Any:
    """Return a chat log view with an optional profile system prompt."""
    if prompt is None:
        return chat_log
    return ProfilePromptedChatLog(chat_log, prompt)


def conversation_profile_chat_turn(
    *,
    entry: Any,
    profile: ConversationProfile,
    entity_id: str,
    chat_log: Any,
) -> ProfileChatTurn:
    """Return a resolved conversation profile chat turn."""
    return ProfileChatTurn(
        entity_id=entity_id,
        client=entry.runtime_data.client,
        model=resolve_conversation_profile_model(entry, profile),
        chat_log=chat_log,
        prompt=profile.prompt,
        max_history=profile.max_history,
        keep_alive=profile.keep_alive,
    )


def ai_task_profile_data_turn(
    *,
    entry: Any,
    profile: AITaskProfile,
    entity_id: str,
    task: Any,
    chat_log: Any,
) -> ProfileChatTurn:
    """Return a resolved AI task profile data-generation chat turn."""
    return ProfileChatTurn(
        entity_id=entity_id,
        client=entry.runtime_data.client,
        model=resolve_ai_task_profile_model(entry, profile),
        chat_log=chat_log_with_profile_prompt(chat_log, profile.prompt),
        structure=getattr(task, "structure", None),
        prompt=profile.prompt,
        max_history=profile.max_history,
        keep_alive=profile.keep_alive,
    )


async def async_execute_conversation_profile_turn(
    *,
    entry: Any,
    profile: ConversationProfile,
    entity_id: str,
    user_input: Any,
    chat_log: Any,
) -> Any:
    """Provide HA LLM data and execute one conversation profile chat turn."""
    turn = conversation_profile_chat_turn(
        entry=entry,
        profile=profile,
        entity_id=entity_id,
        chat_log=chat_log,
    )
    await chat_log.async_provide_llm_data(
        user_input.as_llm_context(DOMAIN),
        profile.hass_api,
        profile.prompt,
        user_input.extra_system_prompt,
    )
    try:
        return await async_execute_chat_log_turn(
            entity_id=turn.entity_id,
            client=turn.client,
            model=turn.model,
            chat_log=turn.chat_log,
            max_history=turn.max_history,
            keep_alive=turn.keep_alive,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise lemonade_home_assistant_error(
            err,
            "Error talking to Lemonade Server",
            timeout_message=None,
        ) from err


async def async_generate_ai_task_profile_data(
    *,
    entry: Any,
    profile: AITaskProfile,
    entity_id: str,
    task: Any,
    chat_log: Any,
) -> Any:
    """Execute one AI task profile data-generation chat turn."""
    turn = ai_task_profile_data_turn(
        entry=entry,
        profile=profile,
        entity_id=entity_id,
        task=task,
        chat_log=chat_log,
    )
    try:
        return await async_generate_chat_log_data(
            entity_id=turn.entity_id,
            client=turn.client,
            model=turn.model,
            chat_log=turn.chat_log,
            structure=turn.structure,
            max_history=turn.max_history,
            keep_alive=turn.keep_alive,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise lemonade_home_assistant_error(
            err,
            "Error generating data with Lemonade",
        ) from err
