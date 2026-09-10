"""Native speech picker contracts against a real Home Assistant runtime."""

from typing import Any

from homeassistant.components import tts
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import pytest


async def test_native_voice_picker_filters_language_and_routes_selected_voice(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
    hass_ws_client: Any,
) -> None:
    """A voice returned by HA's picker reaches Lemonade with its model and locale."""
    _, _, requests = lemonade_entry
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "tts/engine/list"})
    result = await client.receive_json()
    provider = next(p for p in result["result"]["providers"] if p["engine_id"].startswith("tts."))
    engine_id = provider["engine_id"]
    assert "fr" in provider["supported_languages"]
    assert "de" not in provider["supported_languages"]
    await client.send_json({"id": 2, "type": "tts/engine/voices", "engine_id": engine_id, "language": "fr"})
    result = await client.receive_json()
    assert result["success"]
    voices = result["result"]["voices"]
    assert voices and all("kokoro" in voice["name"].lower() for voice in voices)
    french_voice = voices[0]["voice_id"]
    await client.send_json({"id": 3, "type": "tts/engine/voices", "engine_id": engine_id, "language": "en"})
    english = (await client.receive_json())["result"]["voices"]
    assert french_voice not in {voice["voice_id"] for voice in english}
    entity = tts.get_engine_instance(hass, engine_id)
    assert entity is not None
    extension, audio = await entity.async_get_tts_audio("Bonjour", "fr", {"voice": french_voice, "speed": 1.25})
    assert (extension, audio) == ("mp3", b"voice-bytes")
    payload = requests[-1]["payload"]
    assert payload["model"] == "kokoro-v1"
    assert payload["voice"] == "ff_siwis"
    assert payload["lang_code"] == "fr"
    assert payload["speed"] == 1.25
    before = len(requests)
    with pytest.raises(HomeAssistantError):
        await entity.async_get_tts_audio("Hello", "en", {"voice": french_voice})
    assert len(requests) == before


async def test_saved_picker_selection_does_not_fall_back_when_model_is_removed(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
    hass_ws_client: Any,
) -> None:
    """Catalog refresh cannot silently route a selected voice to another model."""
    from dataclasses import replace
    from custom_components.lemonade.models import LemonadeModelCatalog

    entry, _, requests = lemonade_entry
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "tts/engine/list"})
    providers = (await client.receive_json())["result"]["providers"]
    engine_id = next(p["engine_id"] for p in providers if p["engine_id"].startswith("tts."))
    entity = tts.get_engine_instance(hass, engine_id)
    assert entity is not None
    voice = entity.async_get_supported_voices("en")[0]
    coordinator = entry.runtime_data.coordinator
    coordinator.async_set_updated_data(replace(coordinator.data, catalog=LemonadeModelCatalog(())))
    before = len(requests)
    with pytest.raises(HomeAssistantError, match="unavailable"):
        await entity.async_get_tts_audio("Hello", "en", {"voice": voice.voice_id})
    assert len(requests) == before
    assert not entity.async_get_supported_voices("en")
