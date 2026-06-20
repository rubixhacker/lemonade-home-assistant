"""AI task platform for Lemonade Server profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components import ai_task
try:
    from homeassistant.components.conversation import SystemContent
except ImportError:  # pragma: no cover - compatibility with HA module layouts
    from homeassistant.components.conversation.models import SystemContent  # type: ignore[no-redef]
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_IMAGE,
    CONF_DEFAULT_IMAGE_MODEL,
    DOMAIN,
    SUBENTRY_TYPE_AI_TASK,
)
from .data import LemonadeConfigEntry
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .image_result import decode_image_result
from .llm import (
    async_generate_chat_log_data,
    final_assistant_content as _llm_final_assistant_content,
)
from .model_resolution import resolve_entry_model, runtime_model_view
from .profiles import (
    AITaskProfile,
    async_add_profile_entity,
    parse_profile,
    profile_subentries,
    profile_title,
)


@dataclass(frozen=True, slots=True)
class DataGeneration:
    """Resolved Lemonade data-generation invocation."""

    model: str
    chat_log: Any
    structure: Any | None
    prompt: str | None = None
    max_history: int | None = None
    keep_alive: int | None = None


@dataclass(frozen=True, slots=True)
class ImageGeneration:
    """Resolved Lemonade image-generation invocation."""

    model: str
    prompt: str


class _PromptedChatLog:
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade AI task profile entities."""
    for subentry in profile_subentries(entry, SUBENTRY_TYPE_AI_TASK):
        entity = LemonadeAITaskEntity(entry, subentry)
        await async_add_profile_entity(
            async_add_entities,
            entity,
            getattr(subentry, "subentry_id", None),
        )


def _final_assistant_content(chat_log: Any) -> str:
    """Return the latest assistant text from a chat log."""
    return _llm_final_assistant_content(chat_log)


class LemonadeAITaskEntity(ai_task.AITaskEntity):
    """AI task entity backed by a Lemonade AI task profile."""

    _attr_name = None
    _attr_has_entity_name = True

    def __init__(self, entry: LemonadeConfigEntry, subentry: Any) -> None:
        """Initialize the AI task entity."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = getattr(subentry, "subentry_id")
        self._attr_supported_features = (
            ai_task.AITaskEntityFeature.GENERATE_DATA
            | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
        )
        if runtime_model_view(entry).has_models(CAPABILITY_IMAGE):
            self._attr_supported_features |= ai_task.AITaskEntityFeature.GENERATE_IMAGE

        if self._attr_unique_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, self._attr_unique_id)},
                name=profile_title(subentry, getattr(entry, "title", None)),
                manufacturer="Lemonade Server",
                entry_type=DeviceEntryType.SERVICE,
            )

    @property
    def profile(self) -> AITaskProfile:
        """Return the current parsed AI task profile."""
        profile = parse_profile(self.subentry, SUBENTRY_TYPE_AI_TASK)
        assert isinstance(profile, AITaskProfile)
        return profile

    def _resolve_data_model(self, profile: AITaskProfile | None = None) -> str:
        """Return the model configured for this AI task profile."""
        profile = profile or self.profile
        model = resolve_entry_model(
            self.entry,
            CAPABILITY_AI_TASK,
            profile_model=profile.model,
        )
        if model is not None:
            return model

        raise HomeAssistantError("No Lemonade AI task model is available")

    def _resolve_image_model(self, profile: AITaskProfile | None = None) -> str:
        """Return the configured image generation model."""
        profile = profile or self.profile
        model_view = runtime_model_view(self.entry)
        profile_model = profile.model
        if profile_model in model_view.model_ids(CAPABILITY_IMAGE):
            return profile_model

        model = resolve_entry_model(
            self.entry,
            CAPABILITY_IMAGE,
            default_option=CONF_DEFAULT_IMAGE_MODEL,
        )
        if model is not None:
            return model

        raise HomeAssistantError("No Lemonade image model is available")

    def _profile_prompt(self, profile: AITaskProfile | None = None) -> str | None:
        """Return the configured AI task profile prompt."""
        profile = profile or self.profile
        prompt = profile.prompt
        if isinstance(prompt, str):
            prompt = prompt.strip()
            if prompt:
                return prompt
        return None

    def _chat_log_with_profile_prompt(
        self,
        chat_log: Any,
        profile: AITaskProfile,
    ) -> Any:
        """Return a chat log view with the profile prompt as system content."""
        prompt = self._profile_prompt(profile)
        if prompt is None:
            return chat_log
        return _PromptedChatLog(chat_log, prompt)

    def _data_generation(self, task: Any, chat_log: Any) -> DataGeneration:
        """Return a resolved data-generation invocation."""
        profile = self.profile
        prompt = self._profile_prompt(profile)
        return DataGeneration(
            model=self._resolve_data_model(profile),
            chat_log=self._chat_log_with_profile_prompt(chat_log, profile),
            structure=getattr(task, "structure", None),
            prompt=prompt,
            max_history=profile.max_history,
            keep_alive=profile.keep_alive,
        )

    def _image_prompt(
        self,
        task: Any,
        profile: AITaskProfile | None = None,
    ) -> str:
        """Return image instructions with optional profile prompt."""
        task_prompt = getattr(task, "instructions", "")
        if not isinstance(task_prompt, str):
            task_prompt = ""
        task_prompt = task_prompt.strip()
        profile_prompt = self._profile_prompt(profile)
        if profile_prompt is None:
            return task_prompt
        if not task_prompt:
            return profile_prompt
        return f"{profile_prompt}\n\n{task_prompt}"

    def _image_generation(self, task: Any) -> ImageGeneration:
        """Return a resolved image-generation invocation."""
        profile = self.profile
        return ImageGeneration(
            model=self._resolve_image_model(profile),
            prompt=self._image_prompt(task, profile),
        )

    async def _async_generate_data(self, task: Any, chat_log: Any) -> Any:
        """Generate data for an AI task using Lemonade."""
        invocation = self._data_generation(task, chat_log)
        try:
            data = await async_generate_chat_log_data(
                entity_id=getattr(self, "entity_id", None) or self._attr_unique_id,
                client=self.entry.runtime_data.client,
                model=invocation.model,
                chat_log=invocation.chat_log,
                structure=invocation.structure,
                max_history=invocation.max_history,
                keep_alive=invocation.keep_alive,
            )
        except LEMONADE_CLIENT_EXCEPTIONS as err:
            raise lemonade_home_assistant_error(
                err,
                "Error generating data with Lemonade",
            ) from err
        return ai_task.GenDataTaskResult(
            conversation_id=getattr(chat_log, "conversation_id", None),
            data=data,
        )

    async def _async_generate_image(self, task: Any, chat_log: Any) -> Any:
        """Generate an image for an AI task using Lemonade."""
        invocation = self._image_generation(task)
        try:
            response = await self.entry.runtime_data.client.generate_image(
                prompt=invocation.prompt,
                model=invocation.model,
            )
        except LEMONADE_CLIENT_EXCEPTIONS as err:
            raise lemonade_home_assistant_error(
                err,
                "Error generating image with Lemonade",
            ) from err
        image_result = decode_image_result(response)
        if image_result is None:
            raise HomeAssistantError("No image returned")
        return ai_task.GenImageTaskResult(
            image_data=image_result.image_bytes,
            conversation_id=getattr(chat_log, "conversation_id", None),
            mime_type=image_result.mime_type,
            model=invocation.model,
        )
