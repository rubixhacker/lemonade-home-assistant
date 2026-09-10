"""Speech-to-text platform for Lemonade Server."""

from __future__ import annotations

from collections.abc import AsyncIterable
import logging
from typing import Any, assert_never

from homeassistant.components import stt
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import LemonadeConfigEntry
from .speech import (
    SpeechTranscriptionFailure,
    SpeechTranscriptionSuccess,
    resolve_speech_transcription_model,
    transcribe_entry_stream_result,
)
from .server_capabilities import runtime_model_view
from .stt_languages import require_model_language, supported_model_languages

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LemonadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lemonade Server speech-to-text."""
    async_add_entities([LemonadeSTTEntity(entry)])


def _error_result() -> stt.SpeechResult:
    """Return a Home Assistant STT error result."""
    return stt.SpeechResult(None, stt.SpeechResultState.ERROR)


class LemonadeSTTEntity(stt.SpeechToTextEntity):
    """Speech-to-text entity backed by Lemonade Server."""

    _attr_name = "Lemonade Server speech-to-text"
    _attr_has_entity_name = False

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the Lemonade speech-to-text entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stt"

    @property
    def supported_languages(self) -> list[str]:
        """Return locales supported by the currently selected STT model."""
        model = self._resolve_model_record()
        if model is None:
            return []
        return supported_model_languages(model)

    @property
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return supported audio formats."""
        return [stt.AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return supported audio codecs."""
        return [stt.AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return supported bit rates."""
        return [stt.AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return supported sample rates."""
        return [stt.AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return supported audio channels."""
        return [stt.AudioChannels.CHANNEL_MONO]

    def _resolve_model(self) -> str | None:
        """Return the configured or first catalog STT model."""
        return resolve_speech_transcription_model(self.entry)

    def _resolve_model_record(self) -> Any | None:
        """Return the catalog record for the currently selected STT model."""
        model_id = self._resolve_model()
        if model_id is None:
            return None
        return next(
            (
                model
                for model in runtime_model_view(self.entry).catalog.models
                if str(model.id) == model_id
            ),
            None,
        )

    @property
    def available(self) -> bool:
        """Return true when a known-language STT model is available."""
        return bool(self.supported_languages)

    async def async_process_audio_stream(
        self,
        metadata: Any,
        stream: AsyncIterable[bytes],
    ) -> stt.SpeechResult:
        """Transcribe an audio stream with Lemonade Server."""
        model = self._resolve_model()
        if model is None:
            _LOGGER.warning("No Lemonade STT model is available")
            return _error_result()

        model_record = self._resolve_model_record()
        if model_record is None:
            _LOGGER.error("Lemonade STT model %s is not in the runtime catalog", model)
            return _error_result()
        try:
            language = require_model_language(
                model_record,
                getattr(metadata, "language", None),
            )
        except HomeAssistantError as err:
            _LOGGER.error("Cannot transcribe audio with Lemonade: %s", err)
            return _error_result()

        result = await transcribe_entry_stream_result(
            self.entry,
            stream,
            explicit_model=model,
            language=language,
        )
        if isinstance(result, SpeechTranscriptionFailure):
            _LOGGER.error("Error transcribing audio with Lemonade: %s", result.error)
            return _error_result()
        if isinstance(result, SpeechTranscriptionSuccess):
            return stt.SpeechResult(result.text, stt.SpeechResultState.SUCCESS)
        assert_never(result)
