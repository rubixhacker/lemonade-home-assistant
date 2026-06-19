"""Parsed request records for Lemonade direct services."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from homeassistant.const import CONF_MODEL
from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import (
    ATTR_FILENAME,
    ATTR_FILE_PATH,
    ATTR_LANGUAGE,
    ATTR_MAX_TOKENS,
    ATTR_MESSAGES,
    ATTR_PROMPT,
    ATTR_RESPONSE_FORMAT,
    ATTR_SAVE,
    ATTR_SIZE,
    ATTR_SYSTEM_PROMPT,
    ATTR_TEXT,
    ATTR_TEMPERATURE,
    ATTR_VOICE,
    CONF_ENTRY_ID,
)


@dataclass(frozen=True)
class ChatCompletionRequest:
    """Parsed request for lemonade.chat_completion."""

    entry_id: str | None
    model: str | None
    messages: tuple[Mapping[str, Any], ...]
    temperature: Any
    max_tokens: Any

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "ChatCompletionRequest":
        """Parse a Home Assistant service call into a chat request."""
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            messages=_chat_messages(call.data),
            temperature=call.data.get(ATTR_TEMPERATURE),
            max_tokens=call.data.get(ATTR_MAX_TOKENS),
        )


@dataclass(frozen=True)
class GenerateImageRequest:
    """Parsed request for lemonade.generate_image."""

    entry_id: str | None
    model: str | None
    prompt: str
    size: str | None
    save: bool
    filename: str | None

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "GenerateImageRequest":
        """Parse a Home Assistant service call into an image request."""
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            prompt=call.data[ATTR_PROMPT],
            size=call.data.get(ATTR_SIZE),
            save=call.data.get(ATTR_SAVE, False),
            filename=call.data.get(ATTR_FILENAME),
        )


@dataclass(frozen=True)
class TranscribeAudioRequest:
    """Parsed request for lemonade.transcribe_audio."""

    entry_id: str | None
    model: str | None
    file_path: Path
    language: str | None

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "TranscribeAudioRequest":
        """Parse a Home Assistant service call into an audio transcription request."""
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            file_path=Path(call.data[ATTR_FILE_PATH]).resolve(),
            language=call.data.get(ATTR_LANGUAGE),
        )


@dataclass(frozen=True)
class TextToSpeechRequest:
    """Parsed request for lemonade.text_to_speech."""

    entry_id: str | None
    model: str | None
    text: str
    voice: str | None
    response_format: str | None

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "TextToSpeechRequest":
        """Parse a Home Assistant service call into a text-to-speech request."""
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            text=call.data[ATTR_TEXT],
            voice=call.data.get(ATTR_VOICE),
            response_format=call.data.get(ATTR_RESPONSE_FORMAT),
        )


def _chat_messages(data: dict[str, Any]) -> tuple[Mapping[str, Any], ...]:
    """Build OpenAI-compatible chat messages from service data."""
    messages = data.get(ATTR_MESSAGES)
    if messages:
        return tuple(_immutable_message(message) for message in messages)

    prompt = data.get(ATTR_PROMPT)
    if not prompt:
        raise HomeAssistantError(
            f"Either '{ATTR_PROMPT}' or '{ATTR_MESSAGES}' is required"
        )

    built_messages: list[dict[str, Any]] = []
    if system_prompt := data.get(ATTR_SYSTEM_PROMPT):
        built_messages.append({"role": "system", "content": system_prompt})
    built_messages.append({"role": "user", "content": prompt})
    return tuple(_immutable_message(message) for message in built_messages)


def thaw_chat_messages(messages: tuple[Mapping[str, Any], ...]) -> list[dict[str, Any]]:
    """Return mutable OpenAI-compatible chat message payloads."""
    return [_mutable_mapping(message) for message in messages]


def _immutable_message(message: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an immutable copy of one chat message."""
    return _immutable_mapping(message)


def _immutable_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an immutable deep copy of a mapping."""
    return MappingProxyType(
        {key: _immutable_value(mapping_value) for key, mapping_value in value.items()}
    )


def _immutable_value(value: Any) -> Any:
    """Return an immutable deep copy of a service request value."""
    if isinstance(value, Mapping):
        return _immutable_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_immutable_value(item) for item in value)
    return value


def _mutable_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return a mutable deep copy of an immutable mapping."""
    return {key: _mutable_value(mapping_value) for key, mapping_value in value.items()}


def _mutable_value(value: Any) -> Any:
    """Return a mutable deep copy of an immutable request value."""
    if isinstance(value, Mapping):
        return _mutable_mapping(value)
    if isinstance(value, tuple):
        return [_mutable_value(item) for item in value]
    return value
