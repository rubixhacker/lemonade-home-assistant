"""AI task platform for Lemonade Server profiles."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from homeassistant.components import ai_task
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
try:
    from homeassistant.util.json import json_loads
except ImportError:  # pragma: no cover - Home Assistant always provides this
    json_loads = json.loads

from .const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_IMAGE,
    CONF_DEFAULT_AI_TASK_MODEL,
    CONF_DEFAULT_IMAGE_MODEL,
    DOMAIN,
    SUBENTRY_TYPE_AI_TASK,
)
from .data import LemonadeConfigEntry
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .image_result import decode_image_result
from .llm import async_handle_chat_log
from .model_resolution import catalog_model_ids, resolve_entry_model
from .profiles import async_add_profile_entity, profile_data, profile_subentries


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


def _value(obj: Any, name: str, default: Any = None) -> Any:
    """Return a mapping key or attribute value from an object."""
    if isinstance(obj, Mapping) and name in obj:
        return obj[name]
    return getattr(obj, name, default)


def _final_assistant_content(chat_log: Any) -> str:
    """Return the latest assistant text from a chat log."""
    for delta in reversed(getattr(chat_log, "deltas", []) or []):
        content = _value(delta, "content")
        if isinstance(content, str):
            return content

    for content_item in reversed(getattr(chat_log, "content", []) or []):
        role = _value(content_item, "role")
        if role != "assistant":
            continue
        content = _value(content_item, "content")
        if isinstance(content, str):
            return content

    return ""


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
        if catalog_model_ids(entry.runtime_data.coordinator.catalog, CAPABILITY_IMAGE):
            self._attr_supported_features |= ai_task.AITaskEntityFeature.GENERATE_IMAGE

        entry_id = getattr(entry, "entry_id", None)
        if entry_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry_id)},
                name=getattr(entry, "title", None),
                manufacturer="Lemonade Server",
                entry_type=DeviceEntryType.SERVICE,
            )

    def _resolve_data_model(self) -> str:
        """Return the model configured for this AI task profile."""
        data = profile_data(self.subentry)
        model = resolve_entry_model(
            self.entry,
            CAPABILITY_AI_TASK,
            profile_model=data.get(CONF_MODEL),
            default_option=CONF_DEFAULT_AI_TASK_MODEL,
        )
        if model is not None:
            return model

        raise HomeAssistantError("No Lemonade AI task model is available")

    def _resolve_image_model(self) -> str:
        """Return the configured image generation model."""
        model = resolve_entry_model(
            self.entry,
            CAPABILITY_IMAGE,
            default_option=CONF_DEFAULT_IMAGE_MODEL,
        )
        if model is not None:
            return model

        raise HomeAssistantError("No Lemonade image model is available")

    async def _async_generate_data(self, task: Any, chat_log: Any) -> Any:
        """Generate data for an AI task using Lemonade."""
        structure = getattr(task, "structure", None)
        model = self._resolve_data_model()
        try:
            await async_handle_chat_log(
                getattr(self, "entity_id", None) or self._attr_unique_id,
                self.entry.runtime_data.client,
                model,
                chat_log,
                structure=structure,
            )
        except LEMONADE_CLIENT_EXCEPTIONS as err:
            raise lemonade_home_assistant_error(
                err,
                "Error generating data with Lemonade",
            ) from err
        content = _final_assistant_content(chat_log)
        if structure is not None:
            try:
                content = json_loads(content)
            except (TypeError, ValueError) as err:
                raise HomeAssistantError(
                    "Error with Lemonade structured response"
                ) from err
        return ai_task.GenDataTaskResult(
            conversation_id=getattr(chat_log, "conversation_id", None),
            data=content,
        )

    async def _async_generate_image(self, task: Any, chat_log: Any) -> Any:
        """Generate an image for an AI task using Lemonade."""
        image_model = self._resolve_image_model()
        try:
            response = await self.entry.runtime_data.client.generate_image(
                prompt=getattr(task, "instructions", ""),
                model=image_model,
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
            model=image_model,
        )
