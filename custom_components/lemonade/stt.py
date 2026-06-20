"""Speech-to-text platform for Lemonade Server."""

from __future__ import annotations

from collections.abc import AsyncIterable
import logging
from typing import Any

from homeassistant.components import stt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CAPABILITY_STT, CONF_DEFAULT_STT_MODEL, DOMAIN
from .data import LemonadeConfigEntry
from .errors import LEMONADE_CLIENT_EXCEPTIONS
from .model_resolution import resolve_entry_model
from .transcription import transcribe_stream_result

_LOGGER = logging.getLogger(__name__)
_STT_TRANSCRIPTION_EXCEPTIONS = LEMONADE_CLIENT_EXCEPTIONS


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

    _attr_name = "Speech-to-text"
    _attr_has_entity_name = True

    def __init__(self, entry: LemonadeConfigEntry) -> None:
        """Initialize the Lemonade speech-to-text entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stt"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Lemonade Server",
            entry_type=DeviceEntryType.SERVICE,
        )

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

        try:
            result = await transcribe_stream_result(
                self.entry.runtime_data.client,
                stream,
                model=model,
                language=getattr(metadata, "language", None),
            )
        except _STT_TRANSCRIPTION_EXCEPTIONS as err:
            _LOGGER.error("Error transcribing audio with Lemonade: %s", err)
            return _error_result()
        except (KeyError, TypeError) as err:
            _LOGGER.error("Error transcribing audio with Lemonade: %s", err)
            return _error_result()

        return stt.SpeechResult(result.text, stt.SpeechResultState.SUCCESS)
