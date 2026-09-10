"""Behavioral coverage for native TTS language and voice selection."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.lemonade.models import parse_models_response
from custom_components.lemonade.speech_voices import (
    language_matches,
    parse_voice_selection,
    speech_voice_catalog,
    supported_languages,
    voices_for_language,
)


def _kokoro_models(*model_ids: str):
    return parse_models_response(
        {
            "data": [
                {"id": model_id, "recipe": "kokoro", "labels": ["tts"]}
                for model_id in model_ids
            ]
        }
    ).models


def test_kokoro_catalog_matches_authoritative_builtin_voice_count() -> None:
    voices = speech_voice_catalog(_kokoro_models("kokoro-v1"))

    assert len(voices) == 54
    assert voices[0].selection_id == "kokoro-v1::af_heart"
    assert voices[0].name == "kokoro-v1: af_heart"
    assert voices[-1].voice_id == "pm_santa"


def test_language_filter_keeps_regional_voices_separate() -> None:
    models = _kokoro_models("kokoro-v1")

    assert len(voices_for_language(models, "en")) == 28
    assert {voice.language for voice in voices_for_language(models, "en-US")} == {
        "en-US"
    }
    assert {voice.language for voice in voices_for_language(models, "en-GB")} == {
        "en-GB"
    }
    assert len(voices_for_language(models, "fr")) == 1
    assert supported_languages(models)[0:3] == ["en", "en-US", "en-GB"]


def test_non_kokoro_tts_models_do_not_get_invented_voice_choices() -> None:
    models = parse_models_response(
        {"data": [{"id": "OpenMOSS-TTS", "recipe": "moss-tts", "labels": ["tts"]}]}
    ).models

    assert speech_voice_catalog(models) == ()
    assert supported_languages(models) == []
    assert voices_for_language(models, "en") == ()


def test_voice_selection_identity_round_trips_model_and_native_voice() -> None:
    assert parse_voice_selection("kokoro-v1::af_heart") == ("kokoro-v1", "af_heart")
    assert parse_voice_selection("::af_heart") is None
    assert parse_voice_selection("kokoro-v1::") is None
    assert language_matches("en", "en-US")
    assert not language_matches("en-GB", "en-US")


@pytest.mark.asyncio
async def test_picker_voice_binds_model_and_native_voice_at_invocation() -> None:
    from custom_components.lemonade.tts import LemonadeTTSEntity

    class Client:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def text_to_speech(self, **kwargs: object) -> tuple[bytes, str]:
            self.calls.append(kwargs)
            return b"audio", "audio/mpeg"

    client = Client()
    catalog = parse_models_response(
        {
            "data": [
                {"id": "kokoro-v1", "recipe": "kokoro", "labels": ["tts"]},
                {"id": "OpenMOSS-TTS", "recipe": "moss-tts", "labels": ["tts"]},
            ]
        }
    )
    entry = SimpleNamespace(
        entry_id="entry-1",
        options={"default_tts_model": "OpenMOSS-TTS"},
        data={},
        runtime_data=SimpleNamespace(
            client=client,
            coordinator=SimpleNamespace(catalog=catalog),
        ),
    )
    entity = LemonadeTTSEntity(entry)
    picker_voice = entity.async_get_supported_voices("en-US")[0]

    await entity.async_get_tts_audio("Hello", "en-US", {"voice": picker_voice.voice_id})

    assert client.calls[0]["model"] == "kokoro-v1"
    assert client.calls[0]["voice"] == "af_heart"


@pytest.mark.asyncio
async def test_unavailable_picker_voice_requires_another_selection() -> None:
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.lemonade.tts import LemonadeTTSEntity

    catalog = parse_models_response(
        {"data": [{"id": "kokoro-v1", "recipe": "kokoro", "labels": ["tts"]}]}
    )
    entry = SimpleNamespace(
        entry_id="entry-1",
        options={},
        data={},
        runtime_data=SimpleNamespace(
            client=SimpleNamespace(),
            coordinator=SimpleNamespace(catalog=catalog),
        ),
    )
    entity = LemonadeTTSEntity(entry)

    with pytest.raises(HomeAssistantError, match="unavailable"):
        await entity.async_get_tts_audio(
            "Hello", "en", {"voice": "removed-model::af_heart"}
        )


@pytest.mark.asyncio
async def test_picker_voice_rejects_incompatible_language() -> None:
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.lemonade.tts import LemonadeTTSEntity

    catalog = parse_models_response(
        {"data": [{"id": "kokoro-v1", "recipe": "kokoro", "labels": ["tts"]}]}
    )
    entry = SimpleNamespace(
        entry_id="entry-1",
        options={},
        data={},
        runtime_data=SimpleNamespace(
            client=SimpleNamespace(),
            coordinator=SimpleNamespace(catalog=catalog),
        ),
    )
    entity = LemonadeTTSEntity(entry)

    with pytest.raises(HomeAssistantError, match="does not support language"):
        await entity.async_get_tts_audio(
            "Hello", "en-GB", {"voice": "kokoro-v1::af_heart"}
        )


@pytest.mark.asyncio
async def test_picker_voice_rejects_conflicting_explicit_model() -> None:
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.lemonade.tts import LemonadeTTSEntity

    catalog = parse_models_response(
        {
            "data": [
                {"id": "kokoro-v1", "recipe": "kokoro", "labels": ["tts"]},
                {"id": "kokoro-alt", "recipe": "kokoro", "labels": ["tts"]},
            ]
        }
    )
    entry = SimpleNamespace(
        entry_id="entry-1",
        options={},
        data={},
        runtime_data=SimpleNamespace(
            client=SimpleNamespace(),
            coordinator=SimpleNamespace(catalog=catalog),
        ),
    )
    entity = LemonadeTTSEntity(entry)

    with pytest.raises(HomeAssistantError, match="belongs to model"):
        await entity.async_get_tts_audio(
            "Hello",
            "en",
            {"model": "kokoro-alt", "voice": "kokoro-v1::af_heart"},
        )
