"""End-to-end regression coverage for v1.1.1."""

from typing import Any

from homeassistant.components import tts
from homeassistant.core import HomeAssistant


async def test_native_tts_serializes_selected_locale_as_kokoro_lang_code(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """The native TTS path sends its selected locale to Kokoro."""
    _, _, requests = lemonade_entry
    engine = tts.async_default_engine(hass)
    assert engine is not None
    media_source_id = tts.generate_media_source_id(
        hass,
        message="Bonjour tout le monde",
        engine=engine,
        language="fr",
        options={"model": "kokoro-v1"},
        cache=False,
    )

    extension, audio = await tts.async_get_media_source_audio(hass, media_source_id)

    assert (extension, audio) == ("mp3", b"voice-bytes")
    assert requests == [
        {
            "path": "/v1/audio/speech",
            "payload": {
                "input": "Bonjour tout le monde",
                "model": "kokoro-v1",
                "lang_code": "fr",
            },
        }
    ]
