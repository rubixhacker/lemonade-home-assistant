"""Parsed transcription response records for Lemonade."""

from __future__ import annotations

from collections.abc import AsyncIterable, Awaitable, Callable
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_INVALID_TEXT_ERROR = "Lemonade transcription response missing valid text"


@dataclass(frozen=True)
class TranscriptionResult:
    """Validated transcription text returned by Lemonade."""

    text: str


@dataclass(frozen=True)
class TranscriptionRequest:
    """Prepared Lemonade transcription request payload."""

    audio: bytes
    filename: str
    model: str
    language: str | None


@dataclass(frozen=True)
class TranscriptionOutcome:
    """Raw transcription response plus validated text when present."""

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


def parse_transcription_result(response: Any) -> TranscriptionResult:
    """Parse a Lemonade transcription response into a validated result."""
    if not isinstance(response, Mapping):
        raise TypeError(_INVALID_TEXT_ERROR)

    text = response["text"]
    if not isinstance(text, str):
        raise TypeError(_INVALID_TEXT_ERROR)
    return TranscriptionResult(text)


async def file_transcription_request(
    file_path: Path,
    *,
    model: str,
    language: str | None,
    read_file_bytes: Callable[[Path], Awaitable[bytes]],
) -> TranscriptionRequest:
    """Build a transcription request by reading an audio file."""
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    audio = await read_file_bytes(file_path)
    return TranscriptionRequest(
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
) -> TranscriptionRequest:
    """Build a transcription request by buffering an audio stream."""
    audio = b"".join([chunk async for chunk in stream])
    return TranscriptionRequest(
        audio=audio,
        filename=filename,
        model=model,
        language=language,
    )


async def request_transcription(
    client: Any,
    request: TranscriptionRequest,
) -> TranscriptionOutcome:
    """Call Lemonade transcription and capture valid or invalid response shape."""
    response = await client.transcribe_audio(
        audio=request.audio,
        filename=request.filename,
        model=request.model,
        language=request.language,
    )
    return transcription_outcome(response)


async def transcribe_file(
    client: Any,
    file_path: Path,
    *,
    model: str,
    language: str | None,
    read_file_bytes: Callable[[Path], Awaitable[bytes]],
) -> TranscriptionOutcome:
    """Read an audio file, send it to Lemonade, and return the parsed outcome."""
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
    """Buffer an audio stream, send it to Lemonade, and return the parsed outcome."""
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


def transcription_outcome(response: Any) -> TranscriptionOutcome:
    """Parse a transcription response into a reusable outcome record."""
    try:
        result = parse_transcription_result(response)
    except (KeyError, TypeError) as err:
        return TranscriptionOutcome(response=response, result=None, error=err)
    return TranscriptionOutcome(response=response, result=result)
