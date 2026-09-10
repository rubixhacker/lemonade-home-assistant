"""Shared Lemonade speech synthesis and transcription interface."""

from __future__ import annotations

from collections.abc import AsyncIterable, Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import (
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
)
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .server_capabilities import runtime_model_view

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

_SPEECH_SYNTHESIS_ERROR_ACTION = "Error generating speech with Lemonade"
_NO_TTS_MODEL_ERROR = "No Lemonade TTS model is available"
_NO_STT_MODEL_ERROR = "No Lemonade STT model is available"
_INVALID_TEXT_ERROR = "Lemonade transcription response missing valid text"
_MULTILINGUAL_TTS_MIN_SERVER_VERSION = "10.0.1"
_SERVER_VERSION_PATTERN = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)"
    r"(?P<prerelease>-[0-9A-Za-z.-]+)?"
    r"(?:\+[0-9A-Za-z.-]+)?$"
)


def normalize_speech_speed(value: Any) -> float | None:
    """Validate and normalize the optional TTS playback speed."""
    if value is None:
        return None
    try:
        speed = float(value)
    except (TypeError, ValueError) as err:
        raise HomeAssistantError("TTS speed must be between 0.25 and 4.0") from err
    if not 0.25 <= speed <= 4.0:
        raise HomeAssistantError("TTS speed must be between 0.25 and 4.0")
    return speed


@dataclass(frozen=True)
class SpeechSynthesisRequest:
    """Prepared Lemonade text-to-speech request."""

    text: str
    model: str
    voice: str | None
    response_format: str | None
    language: str | None = None
    speed: float | None = None


@dataclass(frozen=True)
class SpeechSynthesisResult:
    """Generated audio plus reusable metadata derived from Lemonade."""

    audio: bytes
    content_type: str | None
    extension: str


@dataclass(frozen=True)
class SpeechTranscriptionRequest:
    """Prepared Lemonade transcription request payload."""

    audio: bytes
    filename: str
    model: str
    language: str | None


@dataclass(frozen=True)
class SpeechTranscriptionSuccess:
    """A valid Lemonade transcription response."""

    text: str
    response: Any


@dataclass(frozen=True)
class SpeechTranscriptionFailure:
    """A transcription failure retained for adapter logging."""

    error: Exception
    response: Any | None = None


SpeechTranscription = SpeechTranscriptionSuccess | SpeechTranscriptionFailure


def resolve_speech_synthesis_model(entry: Any, explicit_model: Any = None) -> str | None:
    """Return the requested, configured, or first catalog TTS model."""
    return runtime_model_view(entry).resolve_entry_model(
        entry,
        CAPABILITY_TTS,
        explicit_model=explicit_model,
        default_option=CONF_DEFAULT_TTS_MODEL,
    )


def require_speech_synthesis_model(entry: Any, explicit_model: Any = None) -> str:
    """Return a TTS model or raise the shared no-model Home Assistant error."""
    model = resolve_speech_synthesis_model(entry, explicit_model)
    if model is not None:
        return model
    raise HomeAssistantError(_NO_TTS_MODEL_ERROR)


def _semantic_version_key(version: str | None) -> tuple[int, int, int, int] | None:
    """Return a comparison key with stable releases after matching prereleases."""
    if version is None:
        return None
    match = _SERVER_VERSION_PATTERN.match(version.strip())
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups()[:3])
    stable = 1 if match.group("prerelease") is None else 0
    return major, minor, patch, stable


def _server_supports_multilingual_tts(entry: Any) -> bool:
    """Return whether the connected server supports Kokoros lang_code."""
    coordinator = getattr(getattr(entry, "runtime_data", None), "coordinator", None)
    version = getattr(coordinator, "server_version", None)
    current = _semantic_version_key(version if isinstance(version, str) else None)
    minimum = _semantic_version_key(_MULTILINGUAL_TTS_MIN_SERVER_VERSION)
    return current is not None and minimum is not None and current >= minimum


def speech_server_supports_multilingual_tts(entry: Any) -> bool:
    """Return whether the connected server accepts non-English TTS locales."""
    return _server_supports_multilingual_tts(entry)


def require_speech_synthesis_language(
    entry: Any,
    language: str | None,
) -> str | None:
    """Return a supported TTS locale or raise for unsupported multilingual TTS."""
    if language is None:
        return None

    if _server_supports_multilingual_tts(entry):
        return language

    if language.strip().lower().replace("_", "-") in {"en", "en-us"}:
        return None

    raise HomeAssistantError(
        "Multilingual TTS requires Lemonade Server "
        f"v{_MULTILINGUAL_TTS_MIN_SERVER_VERSION} or later"
    )


def resolve_speech_transcription_model(
    entry: Any, explicit_model: Any = None
) -> str | None:
    """Return the requested, configured, or first catalog STT model."""
    return runtime_model_view(entry).resolve_entry_model(
        entry,
        CAPABILITY_STT,
        explicit_model=explicit_model,
        default_option=CONF_DEFAULT_STT_MODEL,
    )


def require_speech_transcription_model(entry: Any, explicit_model: Any = None) -> str:
    """Return an STT model or raise the shared no-model Home Assistant error."""
    model = resolve_speech_transcription_model(entry, explicit_model)
    if model is not None:
        return model
    raise HomeAssistantError(_NO_STT_MODEL_ERROR)


def speech_synthesis_request(
    entry: Any,
    *,
    text: str,
    explicit_model: Any = None,
    voice: str | None = None,
    response_format: str | None = None,
    speed: float | None = None,
    language: str | None = None,
) -> SpeechSynthesisRequest:
    """Build a resolved Lemonade speech synthesis request."""
    return SpeechSynthesisRequest(
        text=text,
        model=require_speech_synthesis_model(entry, explicit_model),
        voice=voice,
        response_format=response_format,
        speed=normalize_speech_speed(speed),
        language=require_speech_synthesis_language(entry, language),
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


async def synthesize_speech(
    client: Any,
    request: SpeechSynthesisRequest,
) -> SpeechSynthesisResult:
    """Generate speech audio and translate Lemonade client failures."""
    request_options = {
        "text": request.text,
        "model": request.model,
        "voice": request.voice,
        "response_format": request.response_format,
    }
    if request.speed is not None:
        request_options["speed"] = request.speed
    if request.language is not None:
        request_options["lang_code"] = request.language
    try:
        audio, content_type = await client.text_to_speech(**request_options)
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise lemonade_home_assistant_error(err, _SPEECH_SYNTHESIS_ERROR_ACTION) from err

    return SpeechSynthesisResult(
        audio=audio,
        content_type=content_type,
        extension=audio_extension(content_type, request.response_format),
    )


async def synthesize_entry_speech(
    entry: Any,
    *,
    text: str,
    explicit_model: Any = None,
    voice: str | None = None,
    response_format: str | None = None,
    speed: float | None = None,
    language: str | None = None,
) -> SpeechSynthesisResult:
    """Resolve a config entry model and generate speech audio."""
    request = speech_synthesis_request(
        entry,
        text=text,
        explicit_model=explicit_model,
        voice=voice,
        response_format=response_format,
        speed=speed,
        language=language,
    )
    return await synthesize_speech(entry.runtime_data.client, request)


def speech_transcription_outcome(response: Any) -> SpeechTranscription:
    """Parse a Lemonade response into the closed transcription outcome."""
    try:
        if not isinstance(response, Mapping):
            raise TypeError(_INVALID_TEXT_ERROR)
        text = response["text"]
        if not isinstance(text, str):
            raise TypeError(_INVALID_TEXT_ERROR)
    except (KeyError, TypeError) as err:
        return SpeechTranscriptionFailure(error=err, response=response)
    return SpeechTranscriptionSuccess(text=text, response=response)


async def file_transcription_request(
    file_path: Path,
    *,
    model: str,
    language: str | None,
    read_file_bytes: Callable[[Path], Awaitable[bytes]],
) -> SpeechTranscriptionRequest:
    """Build a transcription request by reading an audio file."""
    if not file_path.is_file():
        raise HomeAssistantError(f"Audio file not found: {file_path}")

    try:
        audio = await read_file_bytes(file_path)
    except FileNotFoundError as err:
        raise HomeAssistantError(f"Audio file not found: {file_path}") from err
    except OSError as err:
        raise HomeAssistantError(f"Could not read audio file: {err}") from err
    return SpeechTranscriptionRequest(
        audio=audio,
        filename=file_path.name,
        model=model,
        language=language,
    )


async def stream_transcription_request(
    stream: AsyncIterable[bytes],
    *,
    model: str,
    language: str | None,
    filename: str = "speech.wav",
) -> SpeechTranscriptionRequest:
    """Build a transcription request by buffering an audio stream."""
    audio = b"".join([chunk async for chunk in stream])
    return SpeechTranscriptionRequest(
        audio=audio,
        filename=filename,
        model=model,
        language=language,
    )


async def request_speech_transcription(
    client: Any,
    request: SpeechTranscriptionRequest,
) -> SpeechTranscription:
    """Call Lemonade transcription and return a typed outcome."""
    response = await client.transcribe_audio(
        audio=request.audio,
        filename=request.filename,
        model=request.model,
        language=request.language,
    )
    return speech_transcription_outcome(response)


async def transcribe_file(
    client: Any,
    file_path: Path,
    *,
    model: str,
    language: str | None,
    read_file_bytes: Callable[[Path], Awaitable[bytes]],
) -> SpeechTranscription:
    """Read an audio file, send it to Lemonade, and return the typed outcome."""
    request = await file_transcription_request(
        file_path,
        model=model,
        language=language,
        read_file_bytes=read_file_bytes,
    )
    return await request_speech_transcription(client, request)


async def transcribe_stream(
    client: Any,
    stream: AsyncIterable[bytes],
    *,
    model: str,
    language: str | None,
    filename: str = "speech.wav",
) -> SpeechTranscription:
    """Buffer an audio stream, send it to Lemonade, and return the typed outcome."""
    request = await stream_transcription_request(
        stream,
        model=model,
        language=language,
        filename=filename,
    )
    return await request_speech_transcription(client, request)


async def transcribe_entry_stream(
    entry: Any,
    stream: AsyncIterable[bytes],
    *,
    explicit_model: Any = None,
    language: str | None,
    filename: str = "speech.wav",
) -> SpeechTranscription:
    """Resolve a config entry model and transcribe a speech stream."""
    return await transcribe_stream(
        entry.runtime_data.client,
        stream,
        model=require_speech_transcription_model(entry, explicit_model),
        language=language,
        filename=filename,
    )


async def transcribe_entry_stream_result(
    entry: Any,
    stream: AsyncIterable[bytes],
    *,
    explicit_model: Any = None,
    language: str | None,
    filename: str = "speech.wav",
) -> SpeechTranscription:
    """Resolve a config entry model and retain client failures as outcomes."""
    try:
        return await transcribe_entry_stream(
            entry,
            stream,
            explicit_model=explicit_model,
            language=language,
            filename=filename,
        )
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        return SpeechTranscriptionFailure(err)
