"""Text-to-speech platform for Lemonade Server."""

from __future__ import annotations

from typing import Any

from homeassistant.components.tts import TextToSpeechEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import LemonadeConfigEntry
from .speech import (
    audio_extension,
    resolve_speech_synthesis_model,
    synthesize_entry_speech,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server text-to-speech."""
    async_add_entities([LemonadeTTSEntity(entry)])


def _audio_extension(content_type: str | None, response_format: Any) -> str:
    """Return a Home Assistant TTS audio extension."""
    return audio_extension(content_type, response_format)


class LemonadeTTSEntity(TextToSpeechEntity):
    """Text-to-speech entity backed by Lemonade Server."""

    _attr_name = "Lemonade Server text-to-speech"
    _attr_has_entity_name = False
    _attr_default_language = "en"
    _attr_supported_languages = ["en"]
    _attr_supported_options = ["voice", "model", "response_format"]

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the Lemonade text-to-speech entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tts"

    def _resolve_model(self, options: dict[str, Any] | None = None) -> str | None:
        """Return the requested, configured, or first catalog TTS model."""
        return resolve_speech_synthesis_model(self.entry, (options or {}).get("model"))

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
        result = await synthesize_entry_speech(
            self.entry,
            text=message,
            explicit_model=options.get("model"),
            voice=options.get("voice"),
            response_format=options.get("response_format"),
        )
        return result.extension, result.audio
