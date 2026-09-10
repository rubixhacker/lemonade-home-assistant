"""Tests for Lemonade speech-to-text model language selection."""

from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

# Reuse the Home Assistant stubs and test fixtures used by the runtime suite.
try:
    from tests.test_runtime import FakeEntry  # noqa: E402
except ModuleNotFoundError:
    from test_runtime import FakeEntry  # noqa: E402

from homeassistant.exceptions import HomeAssistantError  # noqa: E402

from lemonade.models import LemonadeModel, LemonadeModelCatalog, ModelId  # noqa: E402
from lemonade.stt_languages import (  # noqa: E402
    WHISPER_LANGUAGE_CODES,
    language_code,
    model_language_codes,
    require_model_language,
    supported_model_languages,
)


def _model(model_id: str, recipe: str) -> LemonadeModel:
    return LemonadeModel(
        id=ModelId(model_id),
        labels=frozenset({"transcription"}),
        recipe=recipe,
        downloaded=True,
    )


class STTLanguageContractTest(unittest.TestCase):
    def test_known_backends_report_only_their_actual_language_support(self) -> None:
        whisper = _model("Whisper-Tiny", "whispercpp")
        whisper_english = _model("Whisper-Tiny.en", "whispercpp")
        moonshine = _model("Moonshine-Tiny-Streaming", "moonshine")
        unknown = _model("Custom-ASR", "custom-stt")
        flm = _model("Whisper-FLM", "flm")

        self.assertEqual(WHISPER_LANGUAGE_CODES, model_language_codes(whisper))
        self.assertEqual(frozenset({"en"}), model_language_codes(whisper_english))
        self.assertEqual(frozenset({"en"}), model_language_codes(moonshine))
        self.assertIsNone(model_language_codes(unknown))
        self.assertIsNone(model_language_codes(flm))

        ha_languages = {"en", "fr", "pt-BR", "zh-Hant", "es"}
        self.assertEqual(
            ["en", "es", "fr", "pt-BR", "zh-Hant"],
            supported_model_languages(whisper, ha_languages),
        )
        self.assertEqual(["en"], supported_model_languages(moonshine, ha_languages))
        self.assertEqual([], supported_model_languages(unknown, ha_languages))

    def test_locale_is_normalized_to_the_backend_language_code(self) -> None:
        whisper = _model("Whisper-Tiny", "whispercpp")

        self.assertEqual("pt", language_code("pt-BR"))
        self.assertEqual("zh", language_code("zh_Hant"))
        self.assertEqual("no", language_code("nb"))
        self.assertEqual(
            ["fr", "nb"],
            supported_model_languages(whisper, {"nb", "fr"}),
        )
        self.assertEqual(
            "en",
            require_model_language(whisper, "en-GB", {"en-GB", "fr"}),
        )
        self.assertEqual(
            "pt",
            require_model_language(whisper, "pt-BR", {"en", "pt-BR"}),
        )

    def test_unrecognized_whisper_alias_does_not_claim_multilingual_support(self) -> None:
        custom_alias = _model("user.Whisper-Tiny", "whispercpp")

        self.assertIsNone(model_language_codes(custom_alias))
        self.assertEqual([], supported_model_languages(custom_alias, {"en", "fr"}))

    def test_missing_or_unsupported_language_is_rejected(self) -> None:
        moonshine = _model("Moonshine-Tiny-Streaming", "moonshine")

        for language in (None, "", "fr"):
            with self.subTest(language=language):
                with self.assertRaises(HomeAssistantError):
                    require_model_language(moonshine, language, {"en", "fr"})

        with self.assertRaisesRegex(HomeAssistantError, "does not advertise"):
            require_model_language(_model("Custom-ASR", "custom-stt"), "en")


class STTEntityLanguageForwardingTest(unittest.IsolatedAsyncioTestCase):
    async def test_forwards_normalized_explicit_language(self) -> None:
        from lemonade.stt import LemonadeSTTEntity
        from homeassistant.components import stt

        class Client:
            def __init__(self) -> None:
                self.calls: list[dict[str, Any]] = []

            async def transcribe_audio(self, **kwargs: Any) -> dict[str, str]:
                self.calls.append(kwargs)
                return {"text": "bonjour"}

        async def audio_stream() -> Any:
            yield b"audio"

        client = Client()
        entry = FakeEntry()
        entry.options = {}
        entry.runtime_data = SimpleNamespace(
            client=client,
            coordinator=SimpleNamespace(
                catalog=LemonadeModelCatalog((_model("Whisper-Tiny", "whispercpp"),))
            ),
        )
        entity = LemonadeSTTEntity(entry)

        self.assertIn("fr", entity.supported_languages)
        self.assertIn("pt-BR", entity.supported_languages)
        self.assertTrue(entity.available)

        result = await entity.async_process_audio_stream(
            SimpleNamespace(language="pt-BR"), audio_stream()
        )

        self.assertEqual(stt.SpeechResultState.SUCCESS, result.result)
        self.assertEqual("bonjour", result.text)
        self.assertEqual("pt", client.calls[0]["language"])

    async def test_rejects_missing_language_without_calling_backend(self) -> None:
        from lemonade.stt import LemonadeSTTEntity
        from homeassistant.components import stt

        class Client:
            def __init__(self) -> None:
                self.calls = 0

            async def transcribe_audio(self, **kwargs: Any) -> dict[str, str]:
                self.calls += 1
                return {"text": "unexpected"}

        async def audio_stream() -> Any:
            yield b"audio"

        client = Client()
        entry = FakeEntry()
        entry.options = {}
        entry.runtime_data = SimpleNamespace(
            client=client,
            coordinator=SimpleNamespace(
                catalog=LemonadeModelCatalog(
                    (_model("Moonshine-Tiny-Streaming", "moonshine"),)
                )
            ),
        )
        entity = LemonadeSTTEntity(entry)

        result = await entity.async_process_audio_stream(
            SimpleNamespace(language=None), audio_stream()
        )

        self.assertEqual(stt.SpeechResultState.ERROR, result.result)
        self.assertIsNone(result.text)
        self.assertEqual(0, client.calls)
