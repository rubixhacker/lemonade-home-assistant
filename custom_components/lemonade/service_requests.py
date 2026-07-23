"""Parsed request records for Lemonade direct services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    ATTR_ROUTE_TRACE,
    ATTR_ROUTER_METADATA,
    ATTR_RESPONSE_FORMAT,
    ATTR_SAVE,
    ATTR_SIZE,
    ATTR_SYSTEM_PROMPT,
    ATTR_TEXT,
    ATTR_TOP_K,
    ATTR_TEMPERATURE,
    ATTR_VOICE,
    CONF_ENTRY_ID,
)
from .image_result import (
    DirectImageIntent,
    ProduceImageArtifact,
    ReturnRawImageResponse,
)
from .chat_messages import (
    Message,
    MessageParseError,
    SystemMessage,
    UserMessage,
    parse_openai_message,
)


@dataclass(frozen=True)
class ChatCompletionRequest:
    """Parsed request for lemonade.chat_completion."""

    entry_id: str | None
    model: str | None
    messages: tuple[Message, ...]
    temperature: Any
    max_tokens: Any
    route_trace: bool | None
    router_metadata: dict[str, Any] | None

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "ChatCompletionRequest":
        """Parse a Home Assistant service call into a chat request."""
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            messages=_chat_messages(call.data),
            temperature=call.data.get(ATTR_TEMPERATURE),
            max_tokens=call.data.get(ATTR_MAX_TOKENS),
            route_trace=call.data.get(ATTR_ROUTE_TRACE),
            router_metadata=call.data.get(ATTR_ROUTER_METADATA),
        )


@dataclass(frozen=True)
class GenerateImageRequest:
    """Parsed request for lemonade.generate_image."""

    entry_id: str | None
    model: str | None
    prompt: str
    size: str | None
    intent: DirectImageIntent

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "GenerateImageRequest":
        """Parse a Home Assistant service call into an image request."""
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            prompt=call.data[ATTR_PROMPT],
            size=call.data.get(ATTR_SIZE),
            intent=(
                ProduceImageArtifact(filename=call.data.get(ATTR_FILENAME))
                if call.data.get(ATTR_SAVE, False)
                else ReturnRawImageResponse()
            ),
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


@dataclass(frozen=True)
class ClassifyTextRequest:
    """Parsed request for lemonade.classify_text."""

    entry_id: str | None
    model: str | None
    text: str
    top_k: int | None

    @classmethod
    def from_service_call(cls, call: ServiceCall) -> "ClassifyTextRequest":
        """Parse a Home Assistant service call into a classification request."""
        top_k = call.data.get(ATTR_TOP_K)
        if top_k is not None and (
            isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1
        ):
            raise HomeAssistantError("top_k must be a positive integer")
        return cls(
            entry_id=call.data.get(CONF_ENTRY_ID),
            model=call.data.get(CONF_MODEL),
            text=call.data[ATTR_TEXT],
            top_k=top_k,
        )


def _chat_messages(data: dict[str, Any]) -> tuple[Message, ...]:
    """Normalize direct chat messages at the Home Assistant intake seam."""
    messages = data.get(ATTR_MESSAGES)
    if messages:
        try:
            return tuple(parse_openai_message(message) for message in messages)
        except MessageParseError as err:
            raise HomeAssistantError(str(err)) from err

    prompt = data.get(ATTR_PROMPT)
    if not prompt:
        raise HomeAssistantError(
            f"Either '{ATTR_PROMPT}' or '{ATTR_MESSAGES}' is required"
        )

    built_messages: list[Message] = []
    if system_prompt := data.get(ATTR_SYSTEM_PROMPT):
        built_messages.append(SystemMessage(system_prompt))
    built_messages.append(UserMessage(prompt))
    return tuple(built_messages)
