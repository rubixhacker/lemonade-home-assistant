"""Shared Lemonade speech synthesis and transcription interface."""

from __future__ import annotations

from collections.abc import AsyncIterable, Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import (
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
)
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

_SPEECH_SYNTHESIS_ERROR_ACTION = "Error generating speech with Lemonade"
_NO_TTS_MODEL_ERROR = "No Lemonade TTS model is available"
_NO_STT_MODEL_ERROR = "No Lemonade STT model is available"
_INVALID_TEXT_ERROR = "Lemonade transcription response missing valid text"


@dataclass(frozen=True)
class SpeechSynthesisRequest:
    """Prepared Lemonade text-to-speech request."""

    text: str
    model: str
    voice: str | None
    response_format: str | None


@dataclass(frozen=True)
class SpeechSynthesisResult:
    """Generated audio plus reusable metadata derived from Lemonade."""

    audio: bytes
    content_type: str | None
    extension: str


@dataclass(frozen=True)
class SpeechTranscriptionResult:
    """Validated transcription text returned by Lemonade."""

    text: str


@dataclass(frozen=True)
class SpeechTranscriptionRequest:
    """Prepared Lemonade transcription request payload."""

    audio: bytes
    filename: str
    model: str
    language: str | None


@dataclass(frozen=True)
class SpeechTranscription:
    """Typed Lemonade transcription outcome."""

    response: Any

    @property
    def text(self) -> str | None:
        """Return transcribed text when this outcome is valid."""
        raise NotImplementedError

    @property
    def is_valid(self) -> bool:
        """Return true when the response contained valid transcription text."""
        raise NotImplementedError

    def require_result(self) -> SpeechTranscriptionResult:
        """Return the result or re-raise the invalid response error."""
        raise NotImplementedError


@dataclass(frozen=True)
class ValidSpeechTranscription(SpeechTranscription):
    """Transcription outcome with validated text."""

    transcription: SpeechTranscriptionResult

    @property
    def text(self) -> str:
        """Return validated transcription text."""
        return self.transcription.text

    @property
    def is_valid(self) -> bool:
        """Return true for valid transcription text."""
        return True

    def require_result(self) -> SpeechTranscriptionResult:
        """Return the validated transcription result."""
        return self.transcription


@dataclass(frozen=True)
class InvalidSpeechTranscription(SpeechTranscription):
    """Transcription outcome with the parsing failure retained internally."""

    _exception: Exception

    @property
    def text(self) -> None:
        """Return no text for invalid transcription responses."""
        return None

    @property
    def is_valid(self) -> bool:
        """Return false for invalid transcription responses."""
        return False

    def require_result(self) -> SpeechTranscriptionResult:
        """Raise the transcription parsing failure."""
        raise self._exception


def resolve_speech_synthesis_model(entry: Any, explicit_model: Any = None) -> str | None:
    """Return the requested, configured, or first catalog TTS model."""
    return resolve_entry_model(
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


def resolve_speech_transcription_model(
    entry: Any, explicit_model: Any = None
) -> str | None:
    """Return the requested, configured, or first catalog STT model."""
    return resolve_entry_model(
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
) -> SpeechSynthesisRequest:
    """Build a resolved Lemonade speech synthesis request."""
    return SpeechSynthesisRequest(
        text=text,
        model=require_speech_synthesis_model(entry, explicit_model),
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


async def synthesize_speech(
    client: Any,
    request: SpeechSynthesisRequest,
) -> SpeechSynthesisResult:
    """Generate speech audio and translate Lemonade client failures."""
    try:
        audio, content_type = await client.text_to_speech(
            text=request.text,
            model=request.model,
            voice=request.voice,
            response_format=request.response_format,
        )
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
) -> SpeechSynthesisResult:
    """Resolve a config entry model and generate speech audio."""
    request = speech_synthesis_request(
        entry,
        text=text,
        explicit_model=explicit_model,
        voice=voice,
        response_format=response_format,
    )
    return await synthesize_speech(entry.runtime_data.client, request)


def parse_speech_transcription_result(response: Any) -> SpeechTranscriptionResult:
    """Parse a Lemonade transcription response into a validated result."""
    if not isinstance(response, Mapping):
        raise TypeError(_INVALID_TEXT_ERROR)

    text = response["text"]
    if not isinstance(text, str):
        raise TypeError(_INVALID_TEXT_ERROR)
    return SpeechTranscriptionResult(text)


def speech_transcription_outcome(response: Any) -> SpeechTranscription:
    """Parse a transcription response into a valid or invalid outcome record."""
    try:
        result = parse_speech_transcription_result(response)
    except (KeyError, TypeError) as err:
        return InvalidSpeechTranscription(response=response, _exception=err)
    return ValidSpeechTranscription(response=response, transcription=result)


async def file_transcription_request(
    file_path: Path,
    *,
    model: str,
    language: str | None,
    read_file_bytes: Callable[[Path], Awaitable[bytes]],
) -> SpeechTranscriptionRequest:
    """Build a transcription request by reading an audio file."""
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    audio = await read_file_bytes(file_path)
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


async def transcribe_stream_result(
    client: Any,
    stream: AsyncIterable[bytes],
    *,
    model: str,
    language: str | None,
    filename: str = "speech.wav",
) -> SpeechTranscriptionResult:
    """Transcribe a stream and require a valid text result."""
    outcome = await transcribe_stream(
        client,
        stream,
        model=model,
        language=language,
        filename=filename,
    )
    return outcome.require_result()


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
