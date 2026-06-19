"""Custom services for Lemonade Server."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import LemonadeClient
from .data import LemonadeRuntimeData
from .const import (
    ATTR_FILENAME,
    ATTR_FILE_PATH,
    ATTR_LANGUAGE,
    ATTR_MAX_TOKENS,
    ATTR_MEDIA_PATH,
    ATTR_MESSAGES,
    ATTR_PROMPT,
    ATTR_RESPONSE_FORMAT,
    ATTR_SAVE,
    ATTR_SIZE,
    ATTR_SYSTEM_PROMPT,
    ATTR_TEMPERATURE,
    ATTR_TEXT,
    ATTR_VOICE,
    CAPABILITY_CONVERSATION,
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_DEFAULT_CONVERSATION_MODEL,
    CONF_DEFAULT_IMAGE_MODEL,
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
    CONF_ENTRY_ID,
    DOMAIN,
    SERVICE_CHAT_COMPLETION,
    SERVICE_GENERATE_IMAGE,
    SERVICE_TEXT_TO_SPEECH,
    SERVICE_TRANSCRIBE_AUDIO,
)

COMMON_SCHEMA = {
    vol.Optional(CONF_ENTRY_ID): cv.string,
    vol.Optional(CONF_MODEL): cv.string,
}

CHAT_COMPLETION_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Optional(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_SYSTEM_PROMPT): cv.string,
        vol.Optional(ATTR_MESSAGES): [dict],
        vol.Optional(ATTR_TEMPERATURE): vol.Coerce(float),
        vol.Optional(ATTR_MAX_TOKENS): vol.Coerce(int),
    }
)

GENERATE_IMAGE_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Required(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_SIZE): cv.string,
        vol.Optional(ATTR_SAVE, default=False): cv.boolean,
        vol.Optional(ATTR_FILENAME): cv.string,
    }
)

TRANSCRIBE_AUDIO_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Required(ATTR_FILE_PATH): cv.string,
        vol.Optional(ATTR_LANGUAGE): cv.string,
    }
)

TEXT_TO_SPEECH_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_VOICE): cv.string,
        vol.Optional(ATTR_RESPONSE_FORMAT): cv.string,
    }
)

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def _get_entry_and_client(
    hass: HomeAssistant,
    call: ServiceCall,
) -> tuple[ConfigEntry, LemonadeClient]:
    """Return the selected config entry and client for a service call."""
    requested_entry_id = call.data.get(CONF_ENTRY_ID)
    entries = hass.config_entries.async_entries(DOMAIN)

    for entry in entries:
        if requested_entry_id and entry.entry_id != requested_entry_id:
            continue
        runtime_data = getattr(entry, "runtime_data", None)
        if isinstance(runtime_data, LemonadeRuntimeData):
            return entry, runtime_data.client
        if isinstance(runtime_data, LemonadeClient):
            return entry, runtime_data

    if requested_entry_id:
        raise HomeAssistantError(f"Lemonade Server entry is not loaded: {requested_entry_id}")
    raise HomeAssistantError("No loaded Lemonade Server config entry found")


def _first_catalog_model_id(entry: ConfigEntry, capability: str) -> str | None:
    """Return the first model ID in the runtime catalog for a capability."""
    catalog = entry.runtime_data.coordinator.catalog
    if hasattr(catalog, "first_model_id"):
        model = catalog.first_model_id(capability)
        if isinstance(model, str) and model:
            return model
    if hasattr(catalog, "model_ids"):
        model_ids = catalog.model_ids(capability)
        if model_ids:
            return model_ids[0]
    if hasattr(catalog, "models_for"):
        models = catalog.models_for(capability)
        if models:
            model_id = getattr(models[0], "id", None)
            if isinstance(model_id, str) and model_id:
                return model_id
    return None


def _resolve_service_model(
    entry: ConfigEntry,
    requested_model: Any,
    capability: str,
    default_option: str,
    model_label: str,
) -> str:
    """Resolve a direct service model from request, defaults, or catalog."""
    if isinstance(requested_model, str) and requested_model:
        return requested_model

    model = getattr(entry, "options", {}).get(default_option)
    if isinstance(model, str) and model:
        return model

    model = _first_catalog_model_id(entry, capability)
    if isinstance(model, str) and model:
        return model

    raise HomeAssistantError(f"No Lemonade {model_label} model is available")


def _extract_chat_content(response: dict[str, Any]) -> str | None:
    """Extract assistant content from an OpenAI-style chat response."""
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None


def _extension_from_media_type(media_type: str) -> str:
    """Return a safe file extension for an image media type."""
    subtype = media_type.partition("/")[2].split(";", 1)[0].strip().lower()
    if subtype == "jpeg":
        return "jpg"
    subtype = subtype.split("+", 1)[0]
    return _SAFE_FILENAME.sub("_", subtype).strip("._") or "png"


def _decode_base64_image(value: Any, extension: str = "png") -> tuple[bytes | None, str | None]:
    """Decode a base64 image value."""
    if isinstance(value, bytes):
        return value, extension
    if not isinstance(value, str) or not value:
        return None, None

    try:
        return base64.b64decode(value, validate=True), extension
    except (binascii.Error, ValueError):
        return None, None


def _decode_data_image_url(value: Any) -> tuple[bytes | None, str | None]:
    """Decode a data:image/...;base64 URL."""
    if not isinstance(value, str) or not value[:5].lower() == "data:":
        return None, None

    metadata, separator, encoded = value.partition(",")
    if not separator:
        return None, None

    metadata_lower = metadata.lower()
    if not metadata_lower.startswith("data:image/") or ";base64" not in metadata_lower:
        return None, None

    extension = _extension_from_media_type(metadata_lower.removeprefix("data:"))
    return _decode_base64_image(encoded, extension)


def _decode_image_value(value: Any, extension: str = "png") -> tuple[bytes | None, str | None]:
    """Decode an image value that may be base64 or a data URL."""
    image_bytes, image_extension = _decode_data_image_url(value)
    if image_bytes is not None:
        return image_bytes, image_extension
    return _decode_base64_image(value, extension)


def extract_image_bytes(response: Any) -> tuple[bytes | None, str | None]:
    """Extract image bytes and an extension from an image generation response."""
    if not isinstance(response, Mapping):
        return None, None

    first_data: Any = None
    data = response.get("data")
    if isinstance(data, list) and data:
        first_data = data[0]

    if isinstance(first_data, Mapping):
        image_bytes, extension = _decode_base64_image(first_data.get("b64_json"))
        if image_bytes is not None:
            return image_bytes, extension

        image_bytes, extension = _decode_data_image_url(first_data.get("url"))
        if image_bytes is not None:
            return image_bytes, extension

    image_bytes, extension = _decode_base64_image(response.get("b64_json"))
    if image_bytes is not None:
        return image_bytes, extension

    return _decode_image_value(response.get("image"))


def _messages_from_call(call: ServiceCall) -> list[dict[str, Any]]:
    """Build OpenAI-compatible chat messages from service data."""
    messages = call.data.get(ATTR_MESSAGES)
    if messages:
        return list(messages)

    prompt = call.data.get(ATTR_PROMPT)
    if not prompt:
        raise HomeAssistantError(
            f"Either '{ATTR_PROMPT}' or '{ATTR_MESSAGES}' is required"
        )

    built_messages: list[dict[str, Any]] = []
    if system_prompt := call.data.get(ATTR_SYSTEM_PROMPT):
        built_messages.append({"role": "system", "content": system_prompt})
    built_messages.append({"role": "user", "content": prompt})
    return built_messages


def _utcnow_slug() -> str:
    """Return a UTC timestamp slug for generated media filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_media_filename(filename: Any, default_filename: str) -> str:
    """Return a filename safe to place under the Lemonade media directory."""
    if not isinstance(filename, str) or not filename.strip():
        return default_filename

    basename = Path(filename.replace("\\", "/")).name
    basename = _SAFE_FILENAME.sub("_", basename).strip("._")
    if not basename or basename in {".", ".."}:
        return default_filename
    return basename


def _write_image_file(path: Path, image_bytes: bytes) -> None:
    """Create parent directories and write image bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)


async def _async_chat_completion(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.chat_completion."""
    entry, client = _get_entry_and_client(hass, call)
    model = _resolve_service_model(
        entry,
        call.data.get(CONF_MODEL),
        CAPABILITY_CONVERSATION,
        CONF_DEFAULT_CONVERSATION_MODEL,
        "conversation",
    )

    response = await client.chat_completion(
        model=model,
        messages=_messages_from_call(call),
        temperature=call.data.get(ATTR_TEMPERATURE),
        max_tokens=call.data.get(ATTR_MAX_TOKENS),
    )
    return {"content": _extract_chat_content(response), "response": response}


async def _async_generate_image(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.generate_image."""
    entry, client = _get_entry_and_client(hass, call)
    model = _resolve_service_model(
        entry,
        call.data.get(CONF_MODEL),
        CAPABILITY_IMAGE,
        CONF_DEFAULT_IMAGE_MODEL,
        "image",
    )
    response = await client.generate_image(
        prompt=call.data[ATTR_PROMPT],
        model=model,
        size=call.data.get(ATTR_SIZE),
    )
    if not call.data.get(ATTR_SAVE):
        return {"response": response}

    image_bytes, _extension = extract_image_bytes(response)
    if image_bytes is None:
        raise HomeAssistantError(
            "Lemonade image response did not contain image bytes to save"
        )

    default_filename = f"lemonade_{_utcnow_slug()}.png"
    filename = _safe_media_filename(call.data.get(ATTR_FILENAME), default_filename)
    media_dir = hass.config.path("media", "lemonade")
    path = Path(media_dir) / filename
    await hass.async_add_executor_job(_write_image_file, path, image_bytes)
    return {
        "response": response,
        ATTR_MEDIA_PATH: f"media-source://media_source/local/lemonade/{filename}",
    }


async def _async_transcribe_audio(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.transcribe_audio."""
    entry, client = _get_entry_and_client(hass, call)
    model = _resolve_service_model(
        entry,
        call.data.get(CONF_MODEL),
        CAPABILITY_STT,
        CONF_DEFAULT_STT_MODEL,
        "STT",
    )
    file_path = Path(call.data[ATTR_FILE_PATH])
    audio = await hass.async_add_executor_job(file_path.read_bytes)

    response = await client.transcribe_audio(
        audio=audio,
        filename=file_path.name,
        model=model,
        language=call.data.get(ATTR_LANGUAGE),
    )
    text = response.get("text") if isinstance(response.get("text"), str) else None
    return {"text": text, "response": response}


async def _async_text_to_speech(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.text_to_speech."""
    entry, client = _get_entry_and_client(hass, call)
    model = _resolve_service_model(
        entry,
        call.data.get(CONF_MODEL),
        CAPABILITY_TTS,
        CONF_DEFAULT_TTS_MODEL,
        "TTS",
    )
    audio, content_type = await client.text_to_speech(
        text=call.data[ATTR_TEXT],
        model=model,
        voice=call.data.get(ATTR_VOICE),
        response_format=call.data.get(ATTR_RESPONSE_FORMAT),
    )
    return {
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "content_type": content_type,
    }


def async_register_services(hass: HomeAssistant) -> None:
    """Register Lemonade custom services."""

    async def handle_chat_completion(call: ServiceCall) -> dict[str, Any]:
        return await _async_chat_completion(hass, call)

    async def handle_generate_image(call: ServiceCall) -> dict[str, Any]:
        return await _async_generate_image(hass, call)

    async def handle_transcribe_audio(call: ServiceCall) -> dict[str, Any]:
        return await _async_transcribe_audio(hass, call)

    async def handle_text_to_speech(call: ServiceCall) -> dict[str, Any]:
        return await _async_text_to_speech(hass, call)

    if not hass.services.has_service(DOMAIN, SERVICE_CHAT_COMPLETION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHAT_COMPLETION,
            handle_chat_completion,
            schema=CHAT_COMPLETION_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_IMAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_IMAGE,
            handle_generate_image,
            schema=GENERATE_IMAGE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_TRANSCRIBE_AUDIO):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TRANSCRIBE_AUDIO,
            handle_transcribe_audio,
            schema=TRANSCRIBE_AUDIO_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_TEXT_TO_SPEECH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TEXT_TO_SPEECH,
            handle_text_to_speech,
            schema=TEXT_TO_SPEECH_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
