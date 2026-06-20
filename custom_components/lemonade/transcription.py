"""Compatibility adapters for Lemonade speech transcription helpers."""

from __future__ import annotations

from collections.abc import AsyncIterable, Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .speech import (
    InvalidSpeechTranscription,
    SpeechTranscription,
    SpeechTranscriptionRequest as TranscriptionRequest,
    SpeechTranscriptionResult as TranscriptionResult,
    ValidSpeechTranscription,
    file_transcription_request,
    parse_speech_transcription_result as parse_transcription_result,
    request_speech_transcription,
    speech_transcription_outcome,
    stream_transcription_request,
)

_INVALID_TEXT_ERROR = "Lemonade transcription response missing valid text"


@dataclass(frozen=True)
class TranscriptionOutcome:
    """Legacy transcription outcome shape preserved for public callers."""

    response: Any
    result: TranscriptionResult | None
    error: Exception | None = None

    @property
    def text(self) -> str | None:
        """Return transcribed text when the response shape is valid."""
        return self.result.text if self.result is not None else None

    @property
    def is_valid(self) -> bool:
        """Return true when the response contained valid transcription text."""
        return self.result is not None

    def require_result(self) -> TranscriptionResult:
        """Return the result or re-raise the invalid response error."""
        if self.result is not None:
            return self.result
        if self.error is not None:
            raise self.error
        raise TypeError(_INVALID_TEXT_ERROR)


def _legacy_outcome(outcome: SpeechTranscription) -> TranscriptionOutcome:
    """Convert the deeper speech sum type into the legacy adapter record."""
    if isinstance(outcome, ValidSpeechTranscription):
        return TranscriptionOutcome(
            response=outcome.response,
            result=outcome.require_result(),
        )
    if isinstance(outcome, InvalidSpeechTranscription):
        try:
            outcome.require_result()
        except Exception as err:
            return TranscriptionOutcome(
                response=outcome.response,
                result=None,
                error=err,
            )
    raise TypeError(_INVALID_TEXT_ERROR)


def transcription_outcome(response: Any) -> TranscriptionOutcome:
    """Parse a transcription response into the legacy adapter outcome record."""
    return _legacy_outcome(speech_transcription_outcome(response))


async def request_transcription(
    client: Any,
    request: TranscriptionRequest,
) -> TranscriptionOutcome:
    """Call Lemonade transcription and return the legacy adapter outcome."""
    return _legacy_outcome(await request_speech_transcription(client, request))


async def transcribe_file(
    client: Any,
    file_path: Path,
    *,
    model: str,
    language: str | None,
    read_file_bytes: Callable[[Path], Awaitable[bytes]],
) -> TranscriptionOutcome:
    """Read an audio file, send it to Lemonade, and return the legacy outcome."""
    request = await file_transcription_request(
        file_path,
        model=model,
        language=language,
        read_file_bytes=read_file_bytes,
    )
    return await request_transcription(client, request)


async def transcribe_stream(
    client: Any,
    stream: AsyncIterable[bytes],
    *,
    model: str,
    language: str | None,
    filename: str = "speech.wav",
) -> TranscriptionOutcome:
    """Buffer an audio stream, send it to Lemonade, and return the legacy outcome."""
    request = await stream_transcription_request(
        stream,
        model=model,
        language=language,
        filename=filename,
    )
    return await request_transcription(client, request)


async def transcribe_stream_result(
    client: Any,
    stream: AsyncIterable[bytes],
    *,
    model: str,
    language: str | None,
    filename: str = "speech.wav",
) -> TranscriptionResult:
    """Transcribe a stream and require a valid text result."""
    outcome = await transcribe_stream(
        client,
        stream,
        model=model,
        language=language,
        filename=filename,
    )
    return outcome.require_result()
