"""Text-to-speech platform for Lemonade Server."""

from __future__ import annotations

from typing import Any

import aiohttp

from homeassistant.components.tts import TextToSpeechEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LemonadeError
from .const import CAPABILITY_TTS, CONF_DEFAULT_TTS_MODEL
from .data import LemonadeConfigEntry

_CONTENT_TYPE_EXTENSIONS = {
    "audio/aac": "aac",
    "audio/flac": "flac",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/webm": "webm",
    "audio/x-wav": "wav",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server text-to-speech."""
    async_add_entities([LemonadeTTSEntity(entry)])


def _first_catalog_model_id(entry: LemonadeConfigEntry, capability: str) -> str | None:
    """Return the first catalog model ID for a capability."""
    return entry.runtime_data.coordinator.catalog.first_model_id(capability)


def _audio_extension(content_type: str | None, response_format: Any) -> str:
    """Return a Home Assistant TTS audio extension."""
    if isinstance(content_type, str):
        media_type = content_type.partition(";")[0].strip().lower()
        if media_type in _CONTENT_TYPE_EXTENSIONS:
            return _CONTENT_TYPE_EXTENSIONS[media_type]
        if media_type.startswith("audio/"):
            extension = media_type.partition("/")[2]
            if extension.startswith("x-"):
                extension = extension[2:]
            if extension:
                return extension

    if isinstance(response_format, str) and response_format.strip():
        return response_format.strip().lower().lstrip(".")

    return "mp3"


class LemonadeTTSEntity(TextToSpeechEntity):
    """Text-to-speech entity backed by Lemonade Server."""

    _attr_name = None
    _attr_has_entity_name = True
    _attr_default_language = "en"
    _attr_supported_languages = ["en"]
    _attr_supported_options = ["voice", "model", "response_format"]

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the Lemonade text-to-speech entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tts"

    def _resolve_model(self, options: dict[str, Any] | None = None) -> str | None:
        """Return the requested, configured, or first catalog TTS model."""
        option_model = (options or {}).get("model")
        if isinstance(option_model, str) and option_model:
            return option_model

        model = getattr(self.entry, "options", {}).get(CONF_DEFAULT_TTS_MODEL)
        if isinstance(model, str) and model:
            return model

        return _first_catalog_model_id(self.entry, CAPABILITY_TTS)

    @property
    def available(self) -> bool:
        """Return true when a TTS model is available."""
        return self._resolve_model() is not None

    async def async_get_tts_audio(
        self,
        message: str,
        language: str,
        options: dict[str, Any] | None = None,
    ) -> tuple[str, bytes]:
        """Generate speech audio with Lemonade Server."""
        options = options or {}
        model = self._resolve_model(options)
        if model is None:
            raise HomeAssistantError("No Lemonade TTS model is available")

        try:
            audio, content_type = await self.entry.runtime_data.client.text_to_speech(
                text=message,
                model=model,
                voice=options.get("voice"),
                response_format=options.get("response_format"),
            )
        except TimeoutError as err:
            raise HomeAssistantError(
                "Timeout communicating with Lemonade Server"
            ) from err
        except (LemonadeError, aiohttp.ClientError) as err:
            raise HomeAssistantError(
                f"Error generating speech with Lemonade: {err}"
            ) from err

        return _audio_extension(content_type, options.get("response_format")), audio
