"""Parsed transcription response records for Lemonade."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


_INVALID_TEXT_ERROR = "Lemonade transcription response missing valid text"


@dataclass(frozen=True)
class TranscriptionResult:
    """Validated transcription text returned by Lemonade."""

    text: str


def parse_transcription_result(response: Any) -> TranscriptionResult:
    """Parse a Lemonade transcription response into a validated result."""
    if not isinstance(response, Mapping):
        raise TypeError(_INVALID_TEXT_ERROR)

    text = response["text"]
    if not isinstance(text, str):
        raise TypeError(_INVALID_TEXT_ERROR)
    return TranscriptionResult(text)
