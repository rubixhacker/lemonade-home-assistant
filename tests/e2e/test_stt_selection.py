"""STT language selection through the Home Assistant API and HTTP boundary."""

from types import SimpleNamespace
from typing import Any

from homeassistant.components import stt
from homeassistant.core import HomeAssistant


async def test_assistant_language_filters_stt_and_normalizes_backend_request(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
    hass_ws_client: Any,
) -> None:
    """English filtering is HA behavior; changing to French exposes French."""
    _, _, requests = lemonade_entry
    client = await hass_ws_client(hass)
    selections = {}
    for msg_id, language in enumerate(("en", "fr"), 1):
        await client.send_json({"id": msg_id, "type": "stt/engine/list", "language": language})
        result = await client.receive_json()
        assert result["success"]
        provider = next(p for p in result["result"]["providers"] if p["engine_id"].startswith("stt."))
        selections[language] = provider["supported_languages"]
    assert set(selections["en"]) == {"en", "en-GB"}
    assert selections["fr"] == ["fr"]

    entity = stt.async_get_speech_to_text_entity(hass, provider["engine_id"])
    assert entity is not None

    async def audio():
        yield b"\0\0" * 160

    result = await entity.async_process_audio_stream(SimpleNamespace(language="pt-BR"), audio())
    assert result.result is stt.SpeechResultState.SUCCESS
    assert result.text == "bonjour"
    assert requests[-1]["payload"] == {"model": "Whisper-Base", "language": "pt"}
