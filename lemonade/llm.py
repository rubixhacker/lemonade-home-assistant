"""Shared Lemonade LLM conversion helpers."""

from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Iterable, Mapping
import base64
from dataclasses import dataclass
import inspect
import json
from types import MappingProxyType
from typing import Any

from homeassistant.components import conversation
try:
    from homeassistant.components.conversation import (
        AssistantContent,
        AssistantContentDeltaDict,
        SystemContent,
        ToolResultContent,
        UserContent,
    )
except ImportError:  # pragma: no cover - compatibility with HA module layouts
    from homeassistant.components.conversation.models import (  # type: ignore[no-redef]
        AssistantContent,
        AssistantContentDeltaDict,
        SystemContent,
        ToolResultContent,
        UserContent,
    )
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm as hass_llm
try:
    from homeassistant.util.json import json_dumps
except ImportError:  # pragma: no cover - Home Assistant always provides this
    json_dumps = json.dumps
try:
    from homeassistant.util.json import json_loads
except ImportError:  # pragma: no cover - Home Assistant always provides this
    json_loads = json.loads
from voluptuous_openapi import convert

MAX_TOOL_ITERATIONS = 10


_IMAGES_MIME_PREFIX = "image/"


@dataclass(frozen=True)
class ImagePart:
    """Normalized image attachment content for LLM messages."""

    mime_type: str
    url: str


@dataclass(frozen=True)
class ToolCall:
    """Normalized tool call parsed from HA or OpenAI interop shapes."""

    id: str | None
    name: str
    arguments: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", _deep_freeze(self.arguments))


@dataclass(frozen=True)
class ToolResult:
    """Normalized tool result parsed from HA interop shapes."""

    value: Any
    tool_call_id: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _deep_freeze(self.value))


@dataclass(frozen=True)
class Message:
    """Normalized conversation message parsed from HA interop shapes."""

    role: str
    content: str | None = None
    parts: tuple[ImagePart, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    tool_result: ToolResult | None = None


@dataclass(frozen=True)
class ChatTurnRequest:
    """Inputs needed to execute one Lemonade chat turn sequence."""

    entity_id: str
    client: Any
    model: str
    chat_log: Any
    structure: Any | None = None


@dataclass(frozen=True)
class ChatTurnPayload:
    """OpenAI-compatible payload for a Lemonade chat completion request."""

    model: str
    messages: tuple[Mapping[str, Any], ...]
    tools: tuple[Mapping[str, Any], ...] | None = None
    response_format: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", _deep_freeze(self.messages))
        object.__setattr__(self, "tools", _deep_freeze(self.tools))
        object.__setattr__(
            self, "response_format", _deep_freeze(self.response_format)
        )

    def to_chat_completion_kwargs(self) -> dict[str, Any]:
        """Return kwargs accepted by LemonadeClient.chat_completion."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": _jsonable_value(self.messages),
        }
        if self.tools is not None:
            payload["tools"] = _jsonable_value(self.tools)
        if self.response_format is not None:
            payload["response_format"] = _jsonable_value(self.response_format)
        return payload


@dataclass(frozen=True)
class ChatTurnOutcome:
    """Result of applying Lemonade responses to a chat log."""

    iterations: int
    responses: tuple[Mapping[str, Any], ...]
    final_delta: AssistantContentDeltaDict | None
    final_assistant_content: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "responses", _deep_freeze(self.responses))
        object.__setattr__(self, "final_delta", _deep_freeze(self.final_delta))


def _deep_freeze(value: Any) -> Any:
    """Return an immutable copy of nested JSON-like interop payloads."""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _jsonable_value(value: Any) -> Any:
    """Return a JSON-serializable copy of normalized payload values."""
    if isinstance(value, Mapping):
        return {key: _jsonable_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable_value(item) for item in value]
    return value


def _value(obj: Any, *names: str, default: Any = None) -> Any:
    """Return the first present mapping key or attribute from an object."""
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _is_content(content: Any, cls: type[Any], class_name: str) -> bool:
    """Return true if content is an HA content instance by type or name."""
    return isinstance(content, cls) or content.__class__.__name__ == class_name


def _attribute_value(obj: Any, *names: str, default: Any = None) -> Any:
    """Return the first present attribute from an object."""
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _tool_result_json_value(tool_result: Any) -> Any:
    """Return JSON payload without treating mappings as result wrappers."""
    if isinstance(tool_result, Mapping):
        return tool_result
    return _attribute_value(tool_result, "result", default=tool_result)


def format_tool(tool: Any, custom_serializer: Any) -> dict[str, Any]:
    """Format a Home Assistant LLM tool as an OpenAI function tool."""
    function: dict[str, Any] = {
        "name": _value(tool, "name"),
        "parameters": convert(
            _value(tool, "parameters"), custom_serializer=custom_serializer
        ),
    }
    description = _value(tool, "description")
    if description:
        function["description"] = description
    return {"type": "function", "function": function}


def _attachment_mime_type(attachment: Any) -> str:
    """Return an attachment MIME type if available."""
    mime_type = _value(
        attachment,
        "mime_type",
        "content_type",
        "media_content_type",
        "type",
        default="",
    )
    return mime_type if isinstance(mime_type, str) else ""


def _image_url_from_attachment(attachment: Any, mime_type: str) -> str:
    """Return an OpenAI-compatible image URL for an image attachment."""
    url = _value(attachment, "url", "data_url", "content_url")
    if isinstance(url, str) and url:
        return url

    data = _value(attachment, "content", "data", "bytes")
    if isinstance(data, bytes):
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"
    if isinstance(data, str) and data:
        if data.startswith(("data:", "http://", "https://")):
            return data
        return f"data:{mime_type};base64,{data}"

    raise HomeAssistantError("Unsupported image attachment: missing image data")


def _image_part_from_attachment(attachment: Any) -> ImagePart:
    """Parse a user attachment into a normalized image part."""
    mime_type = _attachment_mime_type(attachment)
    if not mime_type.startswith(_IMAGES_MIME_PREFIX):
        raise HomeAssistantError(f"Unsupported attachment type: {mime_type or 'unknown'}")
    return ImagePart(
        mime_type=mime_type,
        url=_image_url_from_attachment(attachment, mime_type),
    )


def _image_part_to_openai(image_part: ImagePart) -> dict[str, Any]:
    """Convert a normalized image part into an OpenAI content part."""
    return {"type": "image_url", "image_url": {"url": image_part.url}}


def _attachment_to_content_part(attachment: Any) -> dict[str, Any]:
    """Convert a user attachment into an OpenAI content part."""
    return _image_part_to_openai(_image_part_from_attachment(attachment))


def _tool_call_record_from_interop(tool_call: Any) -> ToolCall:
    """Parse an OpenAI/HA tool call into a normalized record."""
    tool_call_id = _value(tool_call, "id", "tool_call_id")
    function = _value(tool_call, "function")
    if function is not None:
        name = _value(function, "name")
        arguments = _value(function, "arguments", "args", "tool_args", default={})
        return ToolCall(tool_call_id, name or "", arguments)

    name = _value(tool_call, "name", "tool_name")
    arguments = _value(tool_call, "arguments", "args", "tool_args", "input", default={})
    return ToolCall(tool_call_id, name or "", arguments)


def _extract_tool_call(tool_call: Any) -> tuple[str | None, str | None, Any]:
    """Return an OpenAI/HA tool call's id, name, and arguments."""
    parsed = (
        tool_call if isinstance(tool_call, ToolCall)
        else _tool_call_record_from_interop(tool_call)
    )
    return parsed.id, parsed.name, parsed.arguments


def _arguments_to_json(arguments: Any) -> str:
    """Return tool-call arguments encoded as an OpenAI JSON string."""
    if isinstance(arguments, str):
        return arguments
    if arguments is None:
        arguments = {}
    return json_dumps(_jsonable_value(arguments))


def _tool_call_to_openai(tool_call: Any) -> dict[str, Any]:
    """Convert a Home Assistant tool call to an OpenAI tool_call object."""
    parsed = (
        tool_call if isinstance(tool_call, ToolCall)
        else _tool_call_record_from_interop(tool_call)
    )
    converted = {
        "type": "function",
        "function": {
            "name": parsed.name,
            "arguments": _arguments_to_json(parsed.arguments),
        },
    }
    if parsed.id:
        converted["id"] = parsed.id
    return converted


def _arguments_to_dict(arguments: Any) -> dict[str, Any]:
    """Return tool-call arguments as a mapping for HA ToolInput."""
    if isinstance(arguments, str):
        try:
            loaded = json.loads(arguments)
        except json.JSONDecodeError:
            return {"arguments": arguments}
        return loaded if isinstance(loaded, dict) else {"value": loaded}
    if isinstance(arguments, Mapping):
        return _jsonable_value(arguments)
    if arguments is None:
        return {}
    return {"value": arguments}


def _tool_call_to_tool_input(tool_call: Any) -> Any:
    """Convert an OpenAI tool_call object to a Home Assistant ToolInput."""
    parsed = (
        tool_call if isinstance(tool_call, ToolCall)
        else _tool_call_record_from_interop(tool_call)
    )
    tool_args = _arguments_to_dict(parsed.arguments)
    tool_name = parsed.name

    tool_input = getattr(hass_llm, "ToolInput", None)
    if tool_input is None:
        return {"id": parsed.id, "tool_name": tool_name, "tool_args": tool_args}

    try:
        return tool_input(id=parsed.id, tool_name=tool_name, tool_args=tool_args)
    except TypeError:
        try:
            return tool_input(tool_name=tool_name, tool_args=tool_args)
        except TypeError:
            return tool_input(tool_name, tool_args)


def _content_to_message_record(content: Any) -> Message:
    """Parse Home Assistant conversation content into a normalized message."""
    if _is_content(content, SystemContent, "SystemContent"):
        return Message("system", content=_value(content, "content", default=""))

    if _is_content(content, UserContent, "UserContent"):
        text = _value(content, "content", default="")
        attachments = _value(content, "attachments", default=None) or []
        return Message(
            "user",
            content=text,
            parts=tuple(
                _image_part_from_attachment(attachment) for attachment in attachments
            ),
        )

    if _is_content(content, AssistantContent, "AssistantContent"):
        assistant_content = _value(content, "content")
        tool_calls = _value(content, "tool_calls", default=None) or []
        return Message(
            "assistant",
            content=assistant_content,
            tool_calls=tuple(
                _tool_call_record_from_interop(tool_call) for tool_call in tool_calls
            ),
        )

    if _is_content(content, ToolResultContent, "ToolResultContent"):
        tool_result = _value(
            content, "tool_result", "result", "content", default=None
        )
        return Message(
            "tool",
            tool_result=ToolResult(
                _tool_result_json_value(tool_result),
                tool_call_id=_attribute_value(content, "tool_call_id", "id"),
                name=_attribute_value(content, "tool_name", "name"),
            ),
        )

    raise HomeAssistantError(
        f"Unsupported conversation content: {content.__class__.__name__}"
    )


def _message_record_to_openai(message: Message) -> dict[str, Any]:
    """Convert a normalized message into an OpenAI message."""
    if message.role == "system":
        return {
            "role": "system",
            "content": message.content if message.content is not None else "",
        }

    if message.role == "user":
        if not message.parts:
            return {
                "role": "user",
                "content": message.content if message.content is not None else "",
            }

        parts: list[dict[str, Any]] = []
        if message.content:
            parts.append({"type": "text", "text": message.content})
        parts.extend(_image_part_to_openai(image_part) for image_part in message.parts)
        return {"role": "user", "content": parts}

    if message.role == "assistant":
        converted: dict[str, Any] = {
            "role": "assistant",
            "content": (
                ""
                if message.content is None and not message.tool_calls
                else message.content
            ),
        }
        if message.tool_calls:
            converted["tool_calls"] = [
                _tool_call_to_openai(tool_call) for tool_call in message.tool_calls
            ]
        return converted

    if message.role == "tool" and message.tool_result is not None:
        converted = {
            "role": "tool",
            "content": json_dumps(_jsonable_value(message.tool_result.value)),
        }
        if message.tool_result.tool_call_id:
            converted["tool_call_id"] = message.tool_result.tool_call_id
        if message.tool_result.name:
            converted["name"] = message.tool_result.name
        return converted

    raise HomeAssistantError(f"Unsupported normalized message role: {message.role}")


def content_to_message(content: Any) -> dict[str, Any]:
    """Convert Home Assistant conversation content to an OpenAI message."""
    return _message_record_to_openai(_content_to_message_record(content))


def _response_message(response: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return the first OpenAI response message from a chat completion."""
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, Mapping):
        return None
    message = first.get("message") or first.get("delta")
    return message if isinstance(message, Mapping) else None


def response_to_delta(
    response: Mapping[str, Any],
) -> AssistantContentDeltaDict | None:
    """Return an HA assistant delta from a non-streaming OpenAI chat response."""
    message = _response_message(response)
    if message is None:
        return None

    delta: AssistantContentDeltaDict = {}
    content = message.get("content")
    if content is not None:
        delta["content"] = content

    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        parsed_tool_calls = [
            _tool_call_record_from_interop(tool_call) for tool_call in tool_calls
        ]
        delta["tool_calls"] = [
            _tool_call_to_tool_input(tool_call) for tool_call in parsed_tool_calls
        ]

    return delta or None


async def _async_delta_stream(
    delta: AssistantContentDeltaDict | None,
) -> AsyncIterator[AssistantContentDeltaDict]:
    """Yield one delta through an async iterator for ChatLog."""
    if delta is not None:
        yield delta


async def _async_add_delta_content_stream(
    chat_log: Any,
    entity_id: str,
    delta: AssistantContentDeltaDict | None,
) -> None:
    """Add a non-streaming response delta stream to a chat log."""
    method = chat_log.async_add_delta_content_stream
    try:
        result = method(entity_id, _async_delta_stream(delta))
    except TypeError as original_err:
        try:
            result = method(_async_delta_stream(delta))
        except TypeError:
            raise original_err

    if inspect.isawaitable(result):
        result = await result

    if isinstance(result, AsyncIterable):
        async for _content in result:
            pass


def _iter_llm_tools(llm_api: Any) -> Iterable[Any]:
    """Return tools from an HA LLM API object."""
    tools = _value(llm_api, "tools", default=())
    if isinstance(tools, Mapping):
        return tools.values()
    return tools or ()


def _format_llm_api_tools(llm_api: Any | None) -> list[dict[str, Any]] | None:
    """Return formatted tools for an HA LLM API, if one is provided."""
    if llm_api is None:
        return None
    custom_serializer = _value(llm_api, "custom_serializer")
    return [format_tool(tool, custom_serializer) for tool in _iter_llm_tools(llm_api)]


def _chat_log_messages(chat_log: Any) -> list[dict[str, Any]]:
    """Return OpenAI messages for the current chat log content."""
    return [content_to_message(content) for content in getattr(chat_log, "content", [])]


def _response_format_from_structure(structure: Any) -> Mapping[str, Any]:
    """Return an OpenAI response format for a requested HA structure."""
    if isinstance(structure, Mapping):
        return structure
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "response",
            "schema": convert(structure, custom_serializer=None),
        },
    }


def build_chat_turn_payload(
    model: str,
    chat_log: Any,
    structure: Any | None = None,
) -> ChatTurnPayload:
    """Return a normalized payload record for a chat log turn."""
    tools = _format_llm_api_tools(getattr(chat_log, "llm_api", None))
    response_format = (
        _response_format_from_structure(structure) if structure is not None else None
    )
    return ChatTurnPayload(
        model=model,
        messages=tuple(_chat_log_messages(chat_log)),
        tools=tuple(tools) if tools is not None else None,
        response_format=response_format,
    )


def _build_chat_completion_payload(
    model: str,
    chat_log: Any,
    structure: Any | None = None,
) -> dict[str, Any]:
    """Return the OpenAI chat completion payload for a chat log turn."""
    return build_chat_turn_payload(
        model,
        chat_log,
        structure,
    ).to_chat_completion_kwargs()


async def _apply_chat_response_to_chat_log(
    chat_log: Any,
    entity_id: str,
    response: Mapping[str, Any],
) -> AssistantContentDeltaDict | None:
    """Convert a Lemonade response and append its delta to a chat log."""
    delta = response_to_delta(response)
    await _async_add_delta_content_stream(chat_log, entity_id, delta)
    return delta


def final_assistant_content(chat_log: Any) -> str:
    """Return the latest assistant text from a chat log."""
    for delta in reversed(getattr(chat_log, "deltas", []) or []):
        content = _value(delta, "content")
        if isinstance(content, str):
            return content

    for content_item in reversed(getattr(chat_log, "content", []) or []):
        role = _value(content_item, "role")
        if role != "assistant":
            continue
        content = _value(content_item, "content")
        if isinstance(content, str):
            return content

    return ""


def chat_turn_data(outcome: ChatTurnOutcome, structure: Any | None = None) -> Any:
    """Return a chat-turn text result, parsing structured responses when requested."""
    content = outcome.final_assistant_content
    if structure is None:
        return content
    try:
        return json_loads(content)
    except (TypeError, ValueError) as err:
        raise HomeAssistantError("Error with Lemonade structured response") from err


async def async_execute_chat_turn(request: ChatTurnRequest) -> ChatTurnOutcome:
    """Run Lemonade chat completions until tool results are answered."""
    responses: list[Mapping[str, Any]] = []
    final_delta: AssistantContentDeltaDict | None = None

    for iteration in range(1, MAX_TOOL_ITERATIONS + 1):
        payload = build_chat_turn_payload(
            request.model,
            request.chat_log,
            request.structure,
        )
        response = await request.client.chat_completion(
            **payload.to_chat_completion_kwargs()
        )
        responses.append(response)
        final_delta = await _apply_chat_response_to_chat_log(
            request.chat_log,
            request.entity_id,
            response,
        )

        if not getattr(request.chat_log, "unresponded_tool_results", []):
            return ChatTurnOutcome(
                iterations=iteration,
                responses=tuple(responses),
                final_delta=final_delta,
                final_assistant_content=final_assistant_content(request.chat_log),
            )

    raise HomeAssistantError("Maximum Lemonade tool call iterations reached")


async def async_execute_chat_log_turn(
    *,
    entity_id: str,
    client: Any,
    model: str,
    chat_log: Any,
    structure: Any | None = None,
) -> ChatTurnOutcome:
    """Execute one Lemonade chat log turn, including any required tool loop."""
    return await async_execute_chat_turn(
        ChatTurnRequest(
            entity_id=entity_id,
            client=client,
            model=model,
            chat_log=chat_log,
            structure=structure,
        )
    )


async def async_generate_chat_log_data(
    *,
    entity_id: str,
    client: Any,
    model: str,
    chat_log: Any,
    structure: Any | None = None,
) -> Any:
    """Execute a Lemonade chat log turn and return parsed task data."""
    outcome = await async_execute_chat_log_turn(
        entity_id=entity_id,
        client=client,
        model=model,
        chat_log=chat_log,
        structure=structure,
    )
    return chat_turn_data(outcome, structure)


async def async_handle_chat_log(
    entity_id: str,
    client: Any,
    model: str,
    chat_log: Any,
    structure: Any | None = None,
) -> None:
    """Run Lemonade chat completion turns until tool results are answered."""
    await async_execute_chat_log_turn(
        entity_id=entity_id,
        client=client,
        model=model,
        chat_log=chat_log,
        structure=structure,
    )
