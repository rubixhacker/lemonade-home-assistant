"""Shared Lemonade LLM conversion helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping
import base64
import inspect
import json
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
from voluptuous_openapi import convert

MAX_TOOL_ITERATIONS = 10


_IMAGES_MIME_PREFIX = "image/"


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


def _attachment_to_content_part(attachment: Any) -> dict[str, Any]:
    """Convert a user attachment into an OpenAI content part."""
    mime_type = _attachment_mime_type(attachment)
    if not mime_type.startswith(_IMAGES_MIME_PREFIX):
        raise HomeAssistantError(f"Unsupported attachment type: {mime_type or 'unknown'}")
    return {
        "type": "image_url",
        "image_url": {"url": _image_url_from_attachment(attachment, mime_type)},
    }


def _extract_tool_call(tool_call: Any) -> tuple[str | None, str | None, Any]:
    """Return an OpenAI/HA tool call's id, name, and arguments."""
    tool_call_id = _value(tool_call, "id", "tool_call_id")
    function = _value(tool_call, "function")
    if function is not None:
        name = _value(function, "name")
        arguments = _value(function, "arguments", "args", "tool_args", default={})
        return tool_call_id, name, arguments

    name = _value(tool_call, "name", "tool_name")
    arguments = _value(tool_call, "arguments", "args", "tool_args", "input", default={})
    return tool_call_id, name, arguments


def _arguments_to_json(arguments: Any) -> str:
    """Return tool-call arguments encoded as an OpenAI JSON string."""
    if isinstance(arguments, str):
        return arguments
    if arguments is None:
        arguments = {}
    return json_dumps(arguments)


def _tool_call_to_openai(tool_call: Any) -> dict[str, Any]:
    """Convert a Home Assistant tool call to an OpenAI tool_call object."""
    tool_call_id, name, arguments = _extract_tool_call(tool_call)
    converted = {
        "type": "function",
        "function": {
            "name": name or "",
            "arguments": _arguments_to_json(arguments),
        },
    }
    if tool_call_id:
        converted["id"] = tool_call_id
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
        return dict(arguments)
    if arguments is None:
        return {}
    return {"value": arguments}


def _tool_call_to_tool_input(tool_call: Any) -> Any:
    """Convert an OpenAI tool_call object to a Home Assistant ToolInput."""
    tool_call_id, name, arguments = _extract_tool_call(tool_call)
    tool_args = _arguments_to_dict(arguments)
    tool_name = name or ""

    tool_input = getattr(hass_llm, "ToolInput", None)
    if tool_input is None:
        return {"id": tool_call_id, "tool_name": tool_name, "tool_args": tool_args}

    try:
        return tool_input(id=tool_call_id, tool_name=tool_name, tool_args=tool_args)
    except TypeError:
        try:
            return tool_input(tool_name=tool_name, tool_args=tool_args)
        except TypeError:
            return tool_input(tool_name, tool_args)


def content_to_message(content: Any) -> dict[str, Any]:
    """Convert Home Assistant conversation content to an OpenAI message."""
    if _is_content(content, SystemContent, "SystemContent"):
        return {"role": "system", "content": _value(content, "content", default="")}

    if _is_content(content, UserContent, "UserContent"):
        text = _value(content, "content", default="")
        attachments = _value(content, "attachments", default=None) or []
        if not attachments:
            return {"role": "user", "content": text}

        parts: list[dict[str, Any]] = []
        if text:
            parts.append({"type": "text", "text": text})
        parts.extend(_attachment_to_content_part(attachment) for attachment in attachments)
        return {"role": "user", "content": parts}

    if _is_content(content, AssistantContent, "AssistantContent"):
        assistant_content = _value(content, "content")
        tool_calls = _value(content, "tool_calls", default=None) or []
        message: dict[str, Any] = {
            "role": "assistant",
            "content": (
                ""
                if assistant_content is None and not tool_calls
                else assistant_content
            ),
        }
        if tool_calls:
            message["tool_calls"] = [
                _tool_call_to_openai(tool_call) for tool_call in tool_calls
            ]
        return message

    if _is_content(content, ToolResultContent, "ToolResultContent"):
        tool_result = _value(
            content, "tool_result", "result", "content", default=None
        )
        message = {
            "role": "tool",
            "content": json_dumps(_tool_result_json_value(tool_result)),
        }
        tool_call_id = _attribute_value(content, "tool_call_id", "id")
        if tool_call_id:
            message["tool_call_id"] = tool_call_id
        name = _attribute_value(content, "tool_name", "name")
        if name:
            message["name"] = name
        return message

    raise HomeAssistantError(
        f"Unsupported conversation content: {content.__class__.__name__}"
    )


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
        delta["tool_calls"] = [
            _tool_call_to_tool_input(tool_call) for tool_call in tool_calls
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
        await result


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


async def async_handle_chat_log(
    entity_id: str,
    client: Any,
    model: str,
    chat_log: Any,
    structure: Any | None = None,
) -> None:
    """Run Lemonade chat completion turns until tool results are answered."""
    for _iteration in range(MAX_TOOL_ITERATIONS):
        payload: dict[str, Any] = {
            "model": model,
            "messages": _chat_log_messages(chat_log),
        }
        tools = _format_llm_api_tools(getattr(chat_log, "llm_api", None))
        if tools is not None:
            payload["tools"] = tools
        if structure is not None:
            payload["response_format"] = structure

        response = await client.chat_completion(**payload)
        await _async_add_delta_content_stream(
            chat_log, entity_id, response_to_delta(response)
        )

        if not getattr(chat_log, "unresponded_tool_results", []):
            return

    raise HomeAssistantError("Maximum Lemonade tool call iterations reached")
