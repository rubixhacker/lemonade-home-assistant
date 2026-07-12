"""Home Assistant-independent normalized chat message data and OpenAI adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from types import MappingProxyType
from typing import Any, Literal, TypeAlias, assert_never


class MessageParseError(ValueError):
    """Raised when an OpenAI message does not match a supported variant."""


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


@dataclass(frozen=True)
class ImagePart:
    mime_type: str
    url: str


@dataclass(frozen=True)
class ToolCall:
    id: str | None
    name: str
    arguments: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", _deep_freeze(self.arguments))


@dataclass(frozen=True)
class ToolResult:
    value: Any
    tool_call_id: str | None = None
    name: str | None = None
    content_format: Literal["json", "text"] = "json"

    def __post_init__(self) -> None:
        if self.content_format not in ("json", "text"):
            raise ValueError(f"Unsupported tool result format: {self.content_format}")
        if self.content_format == "text" and not isinstance(self.value, str):
            raise ValueError("Text tool result requires a string value")
        object.__setattr__(self, "value", _deep_freeze(self.value))


@dataclass(frozen=True)
class SystemMessage:
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise ValueError("System message content must be a string")


@dataclass(frozen=True)
class UserMessage:
    content: str
    parts: tuple[ImagePart, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise ValueError("User message content must be a string")
        object.__setattr__(self, "parts", tuple(self.parts))


@dataclass(frozen=True)
class AssistantMessage:
    content: str | None
    tool_calls: tuple[ToolCall, ...] = ()

    def __post_init__(self) -> None:
        if self.content is not None and not isinstance(self.content, str):
            raise ValueError("Assistant message content must be a string or None")
        object.__setattr__(self, "tool_calls", tuple(self.tool_calls))
        if self.content is None and not self.tool_calls:
            raise ValueError("Assistant message requires content or tool calls")


@dataclass(frozen=True)
class ToolResultMessage:
    result: ToolResult


Message: TypeAlias = SystemMessage | UserMessage | AssistantMessage | ToolResultMessage


def _mapping_value(
    value: Mapping[str, Any], *names: str, default: Any = None
) -> Any:
    """Return the first present mapping value, preserving explicit nulls."""
    for name in names:
        if name in value:
            return value[name]
    return default


def _tool_call(raw: Any) -> ToolCall:
    if not isinstance(raw, Mapping):
        raise MessageParseError("Unsupported OpenAI tool call")
    function = raw.get("function")
    source = function if isinstance(function, Mapping) else raw
    name = _mapping_value(source, "name", "tool_name", default="")
    argument_names = (
        ("arguments", "args", "tool_args")
        if isinstance(function, Mapping)
        else ("arguments", "args", "tool_args", "input")
    )
    arguments = _mapping_value(source, *argument_names, default={})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except (TypeError, ValueError):
            pass
    return ToolCall(raw.get("id", raw.get("tool_call_id")), name or "", arguments)


def parse_openai_message(content: Mapping[str, Any]) -> Message:
    """Parse one supported OpenAI message into a closed normalized variant."""
    role = content.get("role")
    message_content = content.get("content")
    if role == "system":
        if not isinstance(message_content, str):
            raise MessageParseError("Unsupported OpenAI system message content")
        return SystemMessage(message_content)
    if role == "user":
        if isinstance(message_content, str) or message_content is None:
            return UserMessage("" if message_content is None else message_content)
        if not isinstance(message_content, (list, tuple)):
            raise MessageParseError("Unsupported OpenAI user message content")
        text_parts: list[str] = []
        image_parts: list[ImagePart] = []
        for part in message_content:
            if not isinstance(part, Mapping):
                raise MessageParseError("Unsupported OpenAI user content part")
            if part.get("type") == "text":
                text = part.get("text")
                if not isinstance(text, str):
                    raise MessageParseError("Unsupported OpenAI user text content part")
                text_parts.append(text)
            elif part.get("type") == "image_url":
                image_url = part.get("image_url")
                url = image_url.get("url") if isinstance(image_url, Mapping) else None
                if not isinstance(url, str) or not url:
                    raise MessageParseError("Unsupported image content part: missing URL")
                mime_type = "image/unknown"
                if url.startswith("data:image/"):
                    mime_type = url[5:].split(";", 1)[0]
                image_parts.append(ImagePart(mime_type, url))
            else:
                raise MessageParseError("Unsupported OpenAI user content part")
        return UserMessage("".join(text_parts), tuple(image_parts))
    if role == "assistant":
        if message_content is not None and not isinstance(message_content, str):
            raise MessageParseError("Unsupported OpenAI assistant message content")
        try:
            return AssistantMessage(
                message_content,
                tuple(_tool_call(call) for call in content.get("tool_calls") or ()),
            )
        except ValueError as err:
            raise MessageParseError("Unsupported OpenAI assistant message content") from err
    if role == "tool":
        value = message_content
        content_format: Literal["json", "text"] = "json"
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                content_format = "text"
        return ToolResultMessage(
            ToolResult(
                value,
                tool_call_id=content.get("tool_call_id", content.get("id")),
                name=content.get("name", content.get("tool_name")),
                content_format=content_format,
            )
        )
    raise MessageParseError(f"Unsupported OpenAI message role: {role}")


def serialize_message(message: Message) -> dict[str, Any]:
    """Serialize one normalized message to an OpenAI-compatible mapping."""
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    if isinstance(message, UserMessage):
        if not message.parts:
            return {"role": "user", "content": message.content}
        parts: list[dict[str, Any]] = []
        if message.content:
            parts.append({"type": "text", "text": message.content})
        parts.extend(
            {"type": "image_url", "image_url": {"url": part.url}}
            for part in message.parts
        )
        return {"role": "user", "content": parts}
    if isinstance(message, AssistantMessage):
        converted: dict[str, Any] = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            converted["tool_calls"] = []
            for call in message.tool_calls:
                arguments = call.arguments
                if not isinstance(arguments, str):
                    arguments = json.dumps(_jsonable({} if arguments is None else arguments))
                raw_call = {
                    "type": "function",
                    "function": {"name": call.name, "arguments": arguments},
                }
                if call.id:
                    raw_call["id"] = call.id
                converted["tool_calls"].append(raw_call)
        return converted
    if isinstance(message, ToolResultMessage):
        result = message.result
        converted = {
            "role": "tool",
            "content": (
                result.value
                if result.content_format == "text"
                else json.dumps(_jsonable(result.value))
            ),
        }
        if result.tool_call_id:
            converted["tool_call_id"] = result.tool_call_id
        if result.name:
            converted["name"] = result.name
        return converted
    assert_never(message)


def response_message(response: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return the first OpenAI response message or delta mapping."""
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, Mapping):
        return None
    message = first.get("message") or first.get("delta")
    return message if isinstance(message, Mapping) else None


def response_assistant_content(response: Mapping[str, Any]) -> str | None:
    """Project first-message assistant text without parsing optional metadata."""
    message = response_message(response)
    if message is None:
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None
