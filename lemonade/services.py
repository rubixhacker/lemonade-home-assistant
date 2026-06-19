"""Custom services for Lemonade Server."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import LemonadeClient
from .data import LemonadeRuntimeData
from .const import (
    ATTR_FILE_PATH,
    ATTR_LANGUAGE,
    ATTR_MAX_TOKENS,
    ATTR_MESSAGES,
    ATTR_PROMPT,
    ATTR_RESPONSE_FORMAT,
    ATTR_SIZE,
    ATTR_SYSTEM_PROMPT,
    ATTR_TEMPERATURE,
    ATTR_TEXT,
    ATTR_VOICE,
    CONF_ENTRY_ID,
    DOMAIN,
    SERVICE_CHAT_COMPLETION,
    SERVICE_GENERATE_IMAGE,
    SERVICE_TEXT_TO_SPEECH,
    SERVICE_TRANSCRIBE_AUDIO,
)

COMMON_SCHEMA = {
    vol.Optional(CONF_ENTRY_ID): cv.string,
    vol.Optional(CONF_MODEL): cv.string,
}

CHAT_COMPLETION_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Optional(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_SYSTEM_PROMPT): cv.string,
        vol.Optional(ATTR_MESSAGES): [dict],
        vol.Optional(ATTR_TEMPERATURE): vol.Coerce(float),
        vol.Optional(ATTR_MAX_TOKENS): vol.Coerce(int),
    }
)

GENERATE_IMAGE_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Required(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_SIZE): cv.string,
    }
)

TRANSCRIBE_AUDIO_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Required(ATTR_FILE_PATH): cv.string,
        vol.Optional(ATTR_LANGUAGE): cv.string,
    }
)

TEXT_TO_SPEECH_SCHEMA = vol.Schema(
    {
        **COMMON_SCHEMA,
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_VOICE): cv.string,
        vol.Optional(ATTR_RESPONSE_FORMAT): cv.string,
    }
)


def _get_entry_and_client(
    hass: HomeAssistant,
    call: ServiceCall,
) -> tuple[ConfigEntry, LemonadeClient]:
    """Return the selected config entry and client for a service call."""
    requested_entry_id = call.data.get(CONF_ENTRY_ID)
    entries = hass.config_entries.async_entries(DOMAIN)

    for entry in entries:
        if requested_entry_id and entry.entry_id != requested_entry_id:
            continue
        runtime_data = getattr(entry, "runtime_data", None)
        if isinstance(runtime_data, LemonadeRuntimeData):
            return entry, runtime_data.client
        if isinstance(runtime_data, LemonadeClient):
            return entry, runtime_data

    if requested_entry_id:
        raise HomeAssistantError(f"Lemonade Server entry is not loaded: {requested_entry_id}")
    raise HomeAssistantError("No loaded Lemonade Server config entry found")


def _default_model(entry: ConfigEntry) -> str | None:
    """Return an entry's configured default model."""
    return entry.options.get(CONF_MODEL) or entry.data.get(CONF_MODEL)


def _extract_chat_content(response: dict[str, Any]) -> str | None:
    """Extract assistant content from an OpenAI-style chat response."""
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None


def _messages_from_call(call: ServiceCall) -> list[dict[str, Any]]:
    """Build OpenAI-compatible chat messages from service data."""
    messages = call.data.get(ATTR_MESSAGES)
    if messages:
        return list(messages)

    prompt = call.data.get(ATTR_PROMPT)
    if not prompt:
        raise HomeAssistantError(
            f"Either '{ATTR_PROMPT}' or '{ATTR_MESSAGES}' is required"
        )

    built_messages: list[dict[str, Any]] = []
    if system_prompt := call.data.get(ATTR_SYSTEM_PROMPT):
        built_messages.append({"role": "system", "content": system_prompt})
    built_messages.append({"role": "user", "content": prompt})
    return built_messages


async def _async_chat_completion(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.chat_completion."""
    entry, client = _get_entry_and_client(hass, call)
    model = call.data.get(CONF_MODEL) or _default_model(entry)
    if not model:
        raise HomeAssistantError("A model is required")

    response = await client.chat_completion(
        model=model,
        messages=_messages_from_call(call),
        temperature=call.data.get(ATTR_TEMPERATURE),
        max_tokens=call.data.get(ATTR_MAX_TOKENS),
    )
    return {"content": _extract_chat_content(response), "response": response}


async def _async_generate_image(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.generate_image."""
    entry, client = _get_entry_and_client(hass, call)
    response = await client.generate_image(
        prompt=call.data[ATTR_PROMPT],
        model=call.data.get(CONF_MODEL) or _default_model(entry),
        size=call.data.get(ATTR_SIZE),
    )
    return {"response": response}


async def _async_transcribe_audio(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.transcribe_audio."""
    entry, client = _get_entry_and_client(hass, call)
    file_path = Path(call.data[ATTR_FILE_PATH])
    audio = await hass.async_add_executor_job(file_path.read_bytes)

    response = await client.transcribe_audio(
        audio=audio,
        filename=file_path.name,
        model=call.data.get(CONF_MODEL) or _default_model(entry),
        language=call.data.get(ATTR_LANGUAGE),
    )
    text = response.get("text") if isinstance(response.get("text"), str) else None
    return {"text": text, "response": response}


async def _async_text_to_speech(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.text_to_speech."""
    entry, client = _get_entry_and_client(hass, call)
    audio, content_type = await client.text_to_speech(
        text=call.data[ATTR_TEXT],
        model=call.data.get(CONF_MODEL) or _default_model(entry),
        voice=call.data.get(ATTR_VOICE),
        response_format=call.data.get(ATTR_RESPONSE_FORMAT),
    )
    return {
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "content_type": content_type,
    }


def async_register_services(hass: HomeAssistant) -> None:
    """Register Lemonade custom services."""

    async def handle_chat_completion(call: ServiceCall) -> dict[str, Any]:
        return await _async_chat_completion(hass, call)

    async def handle_generate_image(call: ServiceCall) -> dict[str, Any]:
        return await _async_generate_image(hass, call)

    async def handle_transcribe_audio(call: ServiceCall) -> dict[str, Any]:
        return await _async_transcribe_audio(hass, call)

    async def handle_text_to_speech(call: ServiceCall) -> dict[str, Any]:
        return await _async_text_to_speech(hass, call)

    if not hass.services.has_service(DOMAIN, SERVICE_CHAT_COMPLETION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHAT_COMPLETION,
            handle_chat_completion,
            schema=CHAT_COMPLETION_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_IMAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_IMAGE,
            handle_generate_image,
            schema=GENERATE_IMAGE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_TRANSCRIBE_AUDIO):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TRANSCRIBE_AUDIO,
            handle_transcribe_audio,
            schema=TRANSCRIBE_AUDIO_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_TEXT_TO_SPEECH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TEXT_TO_SPEECH,
            handle_text_to_speech,
            schema=TEXT_TO_SPEECH_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
