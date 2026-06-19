"""Custom services for Lemonade Server."""

from __future__ import annotations

import base64
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
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .image_result import image_bytes_and_extension
from .model_resolution import resolve_entry_model
from .service_requests import (
    ChatCompletionRequest,
    GenerateImageRequest,
    TextToSpeechRequest,
    TranscribeAudioRequest,
    thaw_chat_messages,
)
from .transcription import parse_transcription_result
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
    requested_entry_id: str | None,
) -> tuple[ConfigEntry, LemonadeClient]:
    """Return the selected config entry and client for a service call."""
    entries = hass.config_entries.async_entries(DOMAIN)

    for entry in entries:
        if requested_entry_id and entry.entry_id != requested_entry_id:
            continue
        runtime_data = getattr(entry, "runtime_data", None)
        if isinstance(runtime_data, LemonadeRuntimeData):
            return entry, runtime_data.client

    if requested_entry_id:
        raise HomeAssistantError(f"Lemonade Server entry is not loaded: {requested_entry_id}")
    raise HomeAssistantError("No loaded Lemonade Server config entry found")


def _resolve_service_model(
    entry: ConfigEntry,
    requested_model: Any,
    capability: str,
    default_option: str,
    model_label: str,
) -> str:
    """Resolve a direct service model from request, defaults, or catalog."""
    model = resolve_entry_model(
        entry,
        capability,
        explicit_model=requested_model,
        default_option=default_option,
    )
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


def extract_image_bytes(response: Any) -> tuple[bytes | None, str | None]:
    """Extract image bytes and an extension from an image generation response."""
    return image_bytes_and_extension(response)


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


def _client_error(err: Exception, action: str) -> HomeAssistantError:
    """Return a Home Assistant service error for a Lemonade client failure."""
    return lemonade_home_assistant_error(err, action)


async def _async_chat_completion(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.chat_completion."""
    request = ChatCompletionRequest.from_service_call(call)
    entry, client = _get_entry_and_client(hass, request.entry_id)
    model = _resolve_service_model(
        entry,
        request.model,
        CAPABILITY_CONVERSATION,
        CONF_DEFAULT_CONVERSATION_MODEL,
        "conversation",
    )

    try:
        response = await client.chat_completion(
            model=model,
            messages=thaw_chat_messages(request.messages),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise _client_error(err, "Error completing chat with Lemonade") from err
    return {"content": _extract_chat_content(response), "response": response}


async def _async_generate_image(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.generate_image."""
    request = GenerateImageRequest.from_service_call(call)
    entry, client = _get_entry_and_client(hass, request.entry_id)
    model = _resolve_service_model(
        entry,
        request.model,
        CAPABILITY_IMAGE,
        CONF_DEFAULT_IMAGE_MODEL,
        "image",
    )
    try:
        response = await client.generate_image(
            prompt=request.prompt,
            model=model,
            size=request.size,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise _client_error(err, "Error generating image with Lemonade") from err
    if not request.save:
        return {"response": response}

    image_bytes, extension = extract_image_bytes(response)
    if image_bytes is None:
        raise HomeAssistantError(
            "Lemonade image response did not contain image bytes to save"
        )

    default_filename = f"lemonade_{_utcnow_slug()}.{extension or 'png'}"
    filename = _safe_media_filename(request.filename, default_filename)
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
    request = TranscribeAudioRequest.from_service_call(call)
    entry, client = _get_entry_and_client(hass, request.entry_id)
    model = _resolve_service_model(
        entry,
        request.model,
        CAPABILITY_STT,
        CONF_DEFAULT_STT_MODEL,
        "STT",
    )
    if not request.file_path.is_file():
        raise HomeAssistantError(f"Audio file not found: {request.file_path}")

    try:
        audio = await hass.async_add_executor_job(request.file_path.read_bytes)
    except OSError as err:
        raise HomeAssistantError(f"Could not read audio file: {err}") from err

    try:
        response = await client.transcribe_audio(
            audio=audio,
            filename=request.file_path.name,
            model=model,
            language=request.language,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise _client_error(err, "Error transcribing audio with Lemonade") from err
    try:
        text = parse_transcription_result(response).text
    except (KeyError, TypeError):
        text = None
    return {"text": text, "response": response}


async def _async_text_to_speech(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.text_to_speech."""
    request = TextToSpeechRequest.from_service_call(call)
    entry, client = _get_entry_and_client(hass, request.entry_id)
    model = _resolve_service_model(
        entry,
        request.model,
        CAPABILITY_TTS,
        CONF_DEFAULT_TTS_MODEL,
        "TTS",
    )
    try:
        audio, content_type = await client.text_to_speech(
            text=request.text,
            model=model,
            voice=request.voice,
            response_format=request.response_format,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise _client_error(err, "Error generating speech with Lemonade") from err
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
