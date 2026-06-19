"""Speech-to-text platform for Lemonade Server."""

from __future__ import annotations

from collections.abc import AsyncIterable
import logging
from typing import Any

from homeassistant.components import stt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CAPABILITY_STT, CONF_DEFAULT_STT_MODEL
from .data import LemonadeConfigEntry
from .errors import LEMONADE_CLIENT_EXCEPTIONS
from .model_resolution import resolve_entry_model
from .transcription import parse_transcription_result

_LOGGER = logging.getLogger(__name__)
_STT_TRANSCRIPTION_EXCEPTIONS = (*LEMONADE_CLIENT_EXCEPTIONS, KeyError, TypeError)


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

    _attr_name = None
    _attr_has_entity_name = True

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the Lemonade speech-to-text entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stt"

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["en"]

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
        return resolve_entry_model(
            self.entry,
            CAPABILITY_STT,
            default_option=CONF_DEFAULT_STT_MODEL,
        )

    @property
    def available(self) -> bool:
        """Return true when an STT model is available."""
        return self._resolve_model() is not None

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

        # Lemonade's transcription endpoint currently accepts multipart file uploads,
        # so buffer the stream before passing it to the client.
        audio = b"".join([chunk async for chunk in stream])
        try:
            response = await self.entry.runtime_data.client.transcribe_audio(
                audio=audio,
                filename="speech.wav",
                model=model,
                language=getattr(metadata, "language", None),
            )
            result = parse_transcription_result(response)
        except _STT_TRANSCRIPTION_EXCEPTIONS as err:
            _LOGGER.error("Error transcribing audio with Lemonade: %s", err)
            return _error_result()

        return stt.SpeechResult(result.text, stt.SpeechResultState.SUCCESS)
