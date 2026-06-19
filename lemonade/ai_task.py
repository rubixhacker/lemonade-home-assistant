"""AI task platform for Lemonade Server profiles."""

from __future__ import annotations

import base64
import binascii
import inspect
import json
from collections.abc import Iterable, Mapping
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
from .llm import async_handle_chat_log


def _subentry_data(subentry: Any) -> dict[str, Any]:
    """Return subentry data as a plain dict."""
    data = getattr(subentry, "data", {}) or {}
    return dict(data) if isinstance(data, dict) else data


def _ai_task_subentries(entry: LemonadeConfigEntry) -> list[Any]:
    """Return AI task profile subentries from a config entry."""
    subentries = getattr(entry, "subentries", {}) or {}
    if isinstance(subentries, dict):
        values = subentries.values()
    else:
        values = subentries
    return [
        subentry
        for subentry in values
        if getattr(subentry, "subentry_type", None) == SUBENTRY_TYPE_AI_TASK
    ]


async def _maybe_await(value: Any) -> None:
    """Await a value only when it is awaitable."""
    if inspect.isawaitable(value):
        await value


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade AI task profile entities."""
    for subentry in _ai_task_subentries(entry):
        entity = LemonadeAITaskEntity(entry, subentry)
        subentry_id = getattr(subentry, "subentry_id", None)
        if subentry_id is None:
            await _maybe_await(async_add_entities([entity]))
            continue
        try:
            result = async_add_entities([entity], config_subentry_id=subentry_id)
        except TypeError:
            result = async_add_entities([entity])
        await _maybe_await(result)


def _catalog_model_ids(entry: LemonadeConfigEntry, capability: str) -> list[str]:
    """Return catalog model IDs for a capability."""
    catalog = entry.runtime_data.coordinator.catalog
    if hasattr(catalog, "model_ids"):
        return list(catalog.model_ids(capability))
    if hasattr(catalog, "models_for"):
        return [model.id for model in catalog.models_for(capability)]
    return []


def _first_catalog_model_id(entry: LemonadeConfigEntry, capability: str) -> str | None:
    """Return the first catalog model ID for a capability."""
    catalog = entry.runtime_data.coordinator.catalog
    if hasattr(catalog, "first_model_id"):
        model = catalog.first_model_id(capability)
        if isinstance(model, str) and model:
            return model
    model_ids = _catalog_model_ids(entry, capability)
    return model_ids[0] if model_ids else None


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
        if role is not None and role != "assistant":
            continue
        content = _value(content_item, "content")
        if isinstance(content, str):
            return content

    return ""


def _image_response_values(response: Any) -> Iterable[Any]:
    """Yield image payload candidates from an OpenAI/Lemonade response."""
    if isinstance(response, Mapping):
        data = response.get("data")
        if isinstance(data, list):
            for item in data:
                yield from _image_response_values(item)
        for key in ("b64_json", "image", "url"):
            if key in response:
                yield response[key]
        return

    if isinstance(response, list):
        for item in response:
            yield from _image_response_values(item)
        return

    yielded_attribute = False
    data = getattr(response, "data", None)
    if isinstance(data, list):
        yielded_attribute = True
        for item in data:
            yield from _image_response_values(item)

    for key in ("b64_json", "image", "url"):
        if hasattr(response, key):
            yielded_attribute = True
            yield getattr(response, key)

    if yielded_attribute:
        return

    yield response


def _decode_image_value(value: Any) -> bytes | None:
    """Decode one image value into bytes when possible."""
    if isinstance(value, bytes):
        return value
    if not isinstance(value, str) or not value:
        return None

    encoded = value
    if value.startswith("data:"):
        _metadata, separator, encoded = value.partition(",")
        if not separator:
            return None

    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None


def _decode_image_response(response: Any) -> bytes | None:
    """Decode the first image bytes from an image generation response."""
    for value in _image_response_values(response):
        image = _decode_image_value(value)
        if image:
            return image
    return None


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
        if _catalog_model_ids(entry, CAPABILITY_IMAGE):
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
        data = _subentry_data(self.subentry)
        model = data.get(CONF_MODEL)
        if isinstance(model, str) and model:
            return model

        model = getattr(self.entry, "options", {}).get(CONF_DEFAULT_AI_TASK_MODEL)
        if isinstance(model, str) and model:
            return model

        model = _first_catalog_model_id(self.entry, CAPABILITY_AI_TASK)
        if isinstance(model, str) and model:
            return model

        raise HomeAssistantError("No Lemonade AI task model is available")

    def _resolve_image_model(self) -> str:
        """Return the configured image generation model."""
        model = getattr(self.entry, "options", {}).get(CONF_DEFAULT_IMAGE_MODEL)
        if isinstance(model, str) and model:
            return model

        model = _first_catalog_model_id(self.entry, CAPABILITY_IMAGE)
        if isinstance(model, str) and model:
            return model

        raise HomeAssistantError("No Lemonade image model is available")

    async def _async_generate_data(self, task: Any, chat_log: Any) -> Any:
        """Generate data for an AI task using Lemonade."""
        structure = getattr(task, "structure", None)
        await async_handle_chat_log(
            getattr(self, "entity_id", None) or self._attr_unique_id,
            self.entry.runtime_data.client,
            self._resolve_data_model(),
            chat_log,
            structure=structure,
        )
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
        response = await self.entry.runtime_data.client.generate_image(
            prompt=getattr(task, "instructions", ""),
            model=image_model,
        )
        image_bytes = _decode_image_response(response)
        if image_bytes is None:
            raise HomeAssistantError("No image returned")
        return ai_task.GenImageTaskResult(
            image_data=image_bytes,
            conversation_id=getattr(chat_log, "conversation_id", None),
            mime_type="image/png",
            model=image_model,
        )
