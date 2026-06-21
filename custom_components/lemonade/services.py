"""Custom services for Lemonade Server."""

from __future__ import annotations

import base64
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import LemonadeClient
from .data import LemonadeRuntimeData
from .errors import LEMONADE_CLIENT_EXCEPTIONS, lemonade_home_assistant_error
from .image_result import (
    ImageGenerationRequest,
    ImageGenerationResult,
    generate_image,
    image_bytes_and_extension,
)
from .model_resolution import resolve_entry_model
from .service_requests import (
    ChatCompletionRequest,
    GenerateImageRequest,
    TextToSpeechRequest,
    TranscribeAudioRequest,
    thaw_chat_messages,
)
from .speech import (
    SpeechSynthesisRequest,
    require_speech_synthesis_model,
    synthesize_speech,
    transcribe_file,
)
from .const import (
    ATTR_FILENAME,
    ATTR_FILE_PATH,
    ATTR_LANGUAGE,
    ATTR_MAX_TOKENS,
    ATTR_MEDIA_PATH,
    ATTR_MESSAGES,
    ATTR_PROMPT,
    ATTR_RESPONSE_FORMAT,
    ATTR_SAVE,
    ATTR_SIZE,
    ATTR_SYSTEM_PROMPT,
    ATTR_TEMPERATURE,
    ATTR_TEXT,
    ATTR_VOICE,
    CAPABILITY_CONVERSATION,
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_DEFAULT_IMAGE_MODEL,
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
    CONF_ENTRY_ID,
    DOMAIN,
    SERVICE_CHAT_COMPLETION,
    SERVICE_GENERATE_IMAGE,
    SERVICE_TEXT_TO_SPEECH,
    SERVICE_TRANSCRIBE_AUDIO,
)

_RequestT = TypeVar("_RequestT")
_ResponseT = TypeVar("_ResponseT")

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
        vol.Optional(ATTR_SAVE, default=False): cv.boolean,
        vol.Optional(ATTR_FILENAME): cv.string,
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


@dataclass(frozen=True)
class DirectServiceContext(Generic[_RequestT]):
    """Resolved direct service request execution context."""

    hass: HomeAssistant
    request: _RequestT
    entry: ConfigEntry
    client: LemonadeClient
    model: str


@dataclass(frozen=True)
class DirectServiceResult(Generic[_RequestT, _ResponseT]):
    """Completed direct service execution with resolved context."""

    context: DirectServiceContext[_RequestT]
    value: _ResponseT


@dataclass(frozen=True)
class DirectServiceRecipe(Generic[_RequestT, _ResponseT]):
    """Direct service execution recipe shared by service handlers."""

    request_factory: Callable[[ServiceCall], _RequestT]
    capability: str
    default_option: str | None
    model_label: str
    error_action: str
    invoke: Callable[[DirectServiceContext[_RequestT]], Awaitable[_ResponseT]]
    resolve_model: Callable[[ConfigEntry, _RequestT], str] | None = None


def _get_entry_and_client(
    hass: HomeAssistant,
    requested_entry_id: str | None,
) -> tuple[ConfigEntry, LemonadeClient]:
    """Return the selected config entry and client for a service call."""
    entries = hass.config_entries.async_entries(DOMAIN)

    for entry in entries:
        if requested_entry_id and entry.entry_id != requested_entry_id:
            continue
        runtime_data = getattr(entry, "runtime_data", None)
        if isinstance(runtime_data, LemonadeRuntimeData):
            return entry, runtime_data.client

    if requested_entry_id:
        raise HomeAssistantError(f"Lemonade Server entry is not loaded: {requested_entry_id}")
    raise HomeAssistantError("No loaded Lemonade Server config entry found")


def _resolve_service_model(
    entry: ConfigEntry,
    requested_model: Any,
    capability: str,
    default_option: str | None,
    model_label: str,
) -> str:
    """Resolve a direct service model from request, defaults, or catalog."""
    model = resolve_entry_model(
        entry,
        capability,
        explicit_model=requested_model,
        default_option=default_option,
    )
    if isinstance(model, str) and model:
        return model

    raise HomeAssistantError(f"No Lemonade {model_label} model is available")


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


def extract_image_bytes(response: Any) -> tuple[bytes | None, str | None]:
    """Extract image bytes and an extension from an image generation response."""
    return image_bytes_and_extension(response)


def _write_image_file(path: Path, image_bytes: bytes) -> None:
    """Create parent directories and write image bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)


def _client_error(err: Exception, action: str) -> HomeAssistantError:
    """Return a Home Assistant service error for a Lemonade client failure."""
    return lemonade_home_assistant_error(err, action)


async def _execute_direct_service(
    hass: HomeAssistant,
    call: ServiceCall,
    *,
    recipe: DirectServiceRecipe[_RequestT, _ResponseT],
) -> DirectServiceResult[_RequestT, _ResponseT]:
    """Parse, resolve, call, and translate errors for a direct service."""
    request = recipe.request_factory(call)
    entry, client = _get_entry_and_client(hass, getattr(request, "entry_id", None))
    if recipe.resolve_model is not None:
        model = recipe.resolve_model(entry, request)
    else:
        model = _resolve_service_model(
            entry,
            getattr(request, "model", None),
            recipe.capability,
            recipe.default_option,
            recipe.model_label,
        )
    context = DirectServiceContext(
        hass=hass,
        request=request,
        entry=entry,
        client=client,
        model=model,
    )
    try:
        value = await recipe.invoke(context)
    except LEMONADE_CLIENT_EXCEPTIONS as err:
        raise _client_error(err, recipe.error_action) from err
    return DirectServiceResult(context=context, value=value)


async def _invoke_chat_completion(
    context: DirectServiceContext[ChatCompletionRequest],
) -> dict[str, Any]:
    """Call Lemonade chat completion for a resolved direct service request."""
    request = context.request
    return await context.client.chat_completion(
        model=context.model,
        messages=thaw_chat_messages(request.messages),
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )


async def _invoke_generate_image(
    context: DirectServiceContext[GenerateImageRequest],
) -> ImageGenerationResult:
    """Call Lemonade image generation for a resolved direct service request."""
    request = context.request
    return await generate_image(
        context.client,
        ImageGenerationRequest(
            prompt=request.prompt,
            model=context.model,
            size=request.size,
            decode_response=request.save,
        ),
    )


async def _invoke_transcribe_audio(
    context: DirectServiceContext[TranscribeAudioRequest],
) -> Any:
    """Transcribe an audio file for a resolved direct service request."""
    request = context.request

    async def read_file_bytes(file_path: Path) -> bytes:
        return await context.hass.async_add_executor_job(file_path.read_bytes)

    return await transcribe_file(
        context.client,
        request.file_path,
        model=context.model,
        language=request.language,
        read_file_bytes=read_file_bytes,
    )


async def _invoke_text_to_speech(
    context: DirectServiceContext[TextToSpeechRequest],
) -> dict[str, Any]:
    """Generate speech for a resolved direct service request."""
    request = context.request
    result = await synthesize_speech(
        context.client,
        SpeechSynthesisRequest(
            text=request.text,
            model=context.model,
            voice=request.voice,
            response_format=request.response_format,
        ),
    )
    return {
        "audio_base64": base64.b64encode(result.audio).decode("ascii"),
        "content_type": result.content_type,
    }


CHAT_COMPLETION_RECIPE = DirectServiceRecipe[
    ChatCompletionRequest, dict[str, Any]
](
    request_factory=ChatCompletionRequest.from_service_call,
    capability=CAPABILITY_CONVERSATION,
    default_option=None,
    model_label="conversation",
    error_action="Error completing chat with Lemonade",
    invoke=_invoke_chat_completion,
)

GENERATE_IMAGE_RECIPE = DirectServiceRecipe[
    GenerateImageRequest, ImageGenerationResult
](
    request_factory=GenerateImageRequest.from_service_call,
    capability=CAPABILITY_IMAGE,
    default_option=CONF_DEFAULT_IMAGE_MODEL,
    model_label="image",
    error_action="Error generating image with Lemonade",
    invoke=_invoke_generate_image,
)

TRANSCRIBE_AUDIO_RECIPE = DirectServiceRecipe[
    TranscribeAudioRequest, Any
](
    request_factory=TranscribeAudioRequest.from_service_call,
    capability=CAPABILITY_STT,
    default_option=CONF_DEFAULT_STT_MODEL,
    model_label="STT",
    error_action="Error transcribing audio with Lemonade",
    invoke=_invoke_transcribe_audio,
)

TEXT_TO_SPEECH_RECIPE = DirectServiceRecipe[
    TextToSpeechRequest, dict[str, Any]
](
    request_factory=TextToSpeechRequest.from_service_call,
    capability=CAPABILITY_TTS,
    default_option=CONF_DEFAULT_TTS_MODEL,
    model_label="TTS",
    error_action="Error generating speech with Lemonade",
    invoke=_invoke_text_to_speech,
    resolve_model=lambda entry, request: require_speech_synthesis_model(
        entry, request.model
    ),
)


async def _async_chat_completion(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.chat_completion."""

    result = await _execute_direct_service(
        hass,
        call,
        recipe=CHAT_COMPLETION_RECIPE,
    )
    response = result.value
    return {"content": _extract_chat_content(response), "response": response}


async def _async_generate_image(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.generate_image."""
    result = await _execute_direct_service(
        hass,
        call,
        recipe=GENERATE_IMAGE_RECIPE,
    )

    request = result.context.request
    image_generation = result.value
    response = image_generation.response
    if not request.save:
        return {"response": response}

    artifact = image_generation.require_artifact(request.filename)
    media_dir = hass.config.path("media", "lemonade")
    path = Path(media_dir) / artifact.filename
    await hass.async_add_executor_job(_write_image_file, path, artifact.image_bytes)
    return {
        "response": response,
        ATTR_MEDIA_PATH: artifact.media_path,
    }


async def _async_transcribe_audio(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.transcribe_audio."""
    result = await _execute_direct_service(
        hass,
        call,
        recipe=TRANSCRIBE_AUDIO_RECIPE,
    )
    outcome = result.value
    return {"text": outcome.text, "response": outcome.response}


async def _async_text_to_speech(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Handle lemonade.text_to_speech."""
    result = await _execute_direct_service(
        hass,
        call,
        recipe=TEXT_TO_SPEECH_RECIPE,
    )
    return result.value


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
