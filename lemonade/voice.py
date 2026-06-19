"""Shared Lemonade voice generation records and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import CAPABILITY_TTS, CONF_DEFAULT_TTS_MODEL
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .model_resolution import resolve_entry_model

_CONTENT_TYPE_EXTENSIONS = {
    "audio/aac": "aac",
    "audio/flac": "flac",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/webm": "webm",
    "audio/x-wav": "wav",
}

_VOICE_ERROR_ACTION = "Error generating speech with Lemonade"
_NO_VOICE_MODEL_ERROR = "No Lemonade TTS model is available"


@dataclass(frozen=True)
class VoiceGenerationRequest:
    """Prepared Lemonade text-to-speech request."""

    text: str
    model: str
    voice: str | None
    response_format: str | None


@dataclass(frozen=True)
class VoiceGenerationResult:
    """Generated audio plus reusable metadata derived from Lemonade."""

    audio: bytes
    content_type: str | None
    extension: str


def resolve_voice_model(entry: Any, explicit_model: Any = None) -> str | None:
    """Return the requested, configured, or first catalog TTS model."""
    return resolve_entry_model(
        entry,
        CAPABILITY_TTS,
        explicit_model=explicit_model,
        default_option=CONF_DEFAULT_TTS_MODEL,
    )


def require_voice_model(entry: Any, explicit_model: Any = None) -> str:
    """Return a TTS model or raise the shared no-model Home Assistant error."""
    model = resolve_voice_model(entry, explicit_model)
    if model is not None:
        return model
    raise HomeAssistantError(_NO_VOICE_MODEL_ERROR)


def voice_generation_request(
    entry: Any,
    *,
    text: str,
    explicit_model: Any = None,
    voice: str | None = None,
    response_format: str | None = None,
) -> VoiceGenerationRequest:
    """Build a resolved Lemonade voice generation request."""
    return VoiceGenerationRequest(
        text=text,
        model=require_voice_model(entry, explicit_model),
        voice=voice,
        response_format=response_format,
    )


def audio_extension(content_type: str | None, response_format: Any) -> str:
    """Return a Home Assistant TTS audio extension."""
    if isinstance(content_type, str):
        media_type = content_type.partition(";")[0].strip().lower()
        if media_type in _CONTENT_TYPE_EXTENSIONS:
            return _CONTENT_TYPE_EXTENSIONS[media_type]
        if media_type.startswith("audio/"):
            extension = media_type.partition("/")[2]
            if extension.startswith("x-"):
                extension = extension[2:]
            if extension:
                return extension

    if isinstance(response_format, str) and response_format.strip():
        return response_format.strip().lower().lstrip(".")

    return "mp3"


async def generate_voice(
    client: Any,
    request: VoiceGenerationRequest,
) -> VoiceGenerationResult:
    """Generate speech audio and translate Lemonade client failures."""
    try:
        audio, content_type = await client.text_to_speech(
            text=request.text,
            model=request.model,
            voice=request.voice,
            response_format=request.response_format,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise lemonade_home_assistant_error(err, _VOICE_ERROR_ACTION) from err

    return VoiceGenerationResult(
        audio=audio,
        content_type=content_type,
        extension=audio_extension(content_type, request.response_format),
    )


async def generate_entry_voice(
    entry: Any,
    *,
    text: str,
    explicit_model: Any = None,
    voice: str | None = None,
    response_format: str | None = None,
) -> VoiceGenerationResult:
    """Resolve a config entry model and generate speech audio."""
    request = voice_generation_request(
        entry,
        text=text,
        explicit_model=explicit_model,
        voice=voice,
        response_format=response_format,
    )
    return await generate_voice(entry.runtime_data.client, request)
