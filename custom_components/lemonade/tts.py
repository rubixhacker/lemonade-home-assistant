"""Text-to-speech platform for Lemonade Server."""

from __future__ import annotations

from typing import Any

from homeassistant.components.tts import TextToSpeechEntity, Voice
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import LemonadeConfigEntry
from .models import Capability
from .server_capabilities import runtime_model_view
from .speech import (
    audio_extension,
    resolve_speech_synthesis_model,
    speech_server_supports_multilingual_tts,
    synthesize_entry_speech,
)
from .speech_voices import (
    find_voice,
    has_voice_selection_marker,
    language_matches,
    parse_voice_selection,
    supported_languages,
    voices_for_language,
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
    _attr_supported_languages: list[str] = []
    _attr_supported_options = ["voice", "model", "response_format", "speed"]

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the Lemonade text-to-speech entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tts"

    def _resolve_model(self, options: dict[str, Any] | None = None) -> str | None:
        """Return the requested, configured, or first catalog TTS model."""
        return resolve_speech_synthesis_model(self.entry, (options or {}).get("model"))

    def _runtime_models(self) -> tuple[Any, ...]:
        """Return the current model records without performing network I/O."""
        return runtime_model_view(self.entry).catalog.models_for(Capability.TTS)

    @property
    def supported_languages(self) -> list[str]:
        """Return languages represented by currently available Kokoro voices."""
        languages = supported_languages(self._runtime_models())
        if speech_server_supports_multilingual_tts(self.entry):
            return languages
        # Unknown versions are handled conservatively by the shared speech
        # helper too. ``en-GB`` is excluded because older servers only accept
        # ``en`` and ``en-US`` without a lang_code extension.
        return [language for language in languages if language in {"en", "en-US"}]

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return model-labelled voices for the selected language."""
        normalized_language = language.strip().replace("_", "-").casefold()
        if (
            not speech_server_supports_multilingual_tts(self.entry)
            and normalized_language not in {"en", "en-us"}
        ):
            return []
        return [
            Voice(voice.selection_id, voice.name_for_language(language))
            for voice in voices_for_language(self._runtime_models(), language)
        ]

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
        explicit_model = options.get("model")
        voice = options.get("voice")
        selected_voice = parse_voice_selection(voice)
        if has_voice_selection_marker(voice) and selected_voice is None:
            raise HomeAssistantError(
                f"Invalid selected TTS voice {voice!r}; choose another voice"
            )
        if selected_voice is not None:
            selected_model, native_voice = selected_voice
            available_voice = find_voice(
                self._runtime_models(), selected_model, native_voice
            )
            if available_voice is None:
                raise HomeAssistantError(
                    f"Selected TTS voice {voice!r} is unavailable; choose another voice"
                )
            if not language_matches(language, available_voice.language):
                raise HomeAssistantError(
                    f"Selected TTS voice {voice!r} does not support "
                    f"language {language!r}"
                )
            if explicit_model is not None and explicit_model != selected_model:
                raise HomeAssistantError(
                    f"Selected TTS voice belongs to model {selected_model!r}, "
                    f"not {explicit_model!r}"
                )
            # The picker ID carries the model, so retain that model even when
            # the Server Entry's default changes between selection and use.
            explicit_model = selected_model
            voice = native_voice
        result = await synthesize_entry_speech(
            self.entry,
            text=message,
            explicit_model=explicit_model,
            voice=voice,
            response_format=options.get("response_format"),
            speed=options.get("speed"),
            language=language,
        )
        return result.extension, result.audio
