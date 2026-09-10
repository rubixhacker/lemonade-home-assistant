"""Speech voice catalogues with stable model-bound voice selections."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


# Catalog: https://huggingface.co/hexgrad/Kokoro-82M/blob/c3327e9/VOICES.md
# Lemonade serves the voices-v1.0.bin pack via https://github.com/lemonade-sdk/Kokoros
# These are the built-in voices shipped by Kokoro-82M.  The language values
# are BCP-47 tags used by Home Assistant; the Kokoro pipeline code is derived
# by Lemonade/Kokoros from the voice prefix at request time.
_KOKORO_VOICE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    # American English (lang_code=a)
    ("af_heart", "en-US"),
    ("af_alloy", "en-US"),
    ("af_aoede", "en-US"),
    ("af_bella", "en-US"),
    ("af_jessica", "en-US"),
    ("af_kore", "en-US"),
    ("af_nicole", "en-US"),
    ("af_nova", "en-US"),
    ("af_river", "en-US"),
    ("af_sarah", "en-US"),
    ("af_sky", "en-US"),
    ("am_adam", "en-US"),
    ("am_echo", "en-US"),
    ("am_eric", "en-US"),
    ("am_fenrir", "en-US"),
    ("am_liam", "en-US"),
    ("am_michael", "en-US"),
    ("am_onyx", "en-US"),
    ("am_puck", "en-US"),
    ("am_santa", "en-US"),
    # British English (lang_code=b)
    ("bf_alice", "en-GB"),
    ("bf_emma", "en-GB"),
    ("bf_isabella", "en-GB"),
    ("bf_lily", "en-GB"),
    ("bm_daniel", "en-GB"),
    ("bm_fable", "en-GB"),
    ("bm_george", "en-GB"),
    ("bm_lewis", "en-GB"),
    # Japanese (lang_code=j)
    ("jf_alpha", "ja-JP"),
    ("jf_gongitsune", "ja-JP"),
    ("jf_nezumi", "ja-JP"),
    ("jf_tebukuro", "ja-JP"),
    ("jm_kumo", "ja-JP"),
    # Mandarin Chinese (lang_code=z)
    ("zf_xiaobei", "zh-CN"),
    ("zf_xiaoni", "zh-CN"),
    ("zf_xiaoxiao", "zh-CN"),
    ("zf_xiaoyi", "zh-CN"),
    ("zm_yunjian", "zh-CN"),
    ("zm_yunxi", "zh-CN"),
    ("zm_yunxia", "zh-CN"),
    ("zm_yunyang", "zh-CN"),
    # Spanish (lang_code=e)
    ("ef_dora", "es-ES"),
    ("em_alex", "es-ES"),
    ("em_santa", "es-ES"),
    # French (lang_code=f)
    ("ff_siwis", "fr-FR"),
    # Hindi (lang_code=h)
    ("hf_alpha", "hi-IN"),
    ("hf_beta", "hi-IN"),
    ("hm_omega", "hi-IN"),
    ("hm_psi", "hi-IN"),
    # Italian (lang_code=i)
    ("if_sara", "it-IT"),
    ("im_nicola", "it-IT"),
    # Brazilian Portuguese (lang_code=p)
    ("pf_dora", "pt-BR"),
    ("pm_alex", "pt-BR"),
    ("pm_santa", "pt-BR"),
)

# Include the primary language tags so a user selecting ``en`` sees both
# American and British voices. Regional tags remain available for callers
# that need to distinguish the two English pipelines.
KOKORO_SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "en",
    "en-US",
    "en-GB",
    "es",
    "es-ES",
    "fr",
    "fr-FR",
    "hi",
    "hi-IN",
    "it",
    "it-IT",
    "ja",
    "ja-JP",
    "pt",
    "pt-BR",
    "zh",
    "zh-CN",
)

VOICE_ID_SEPARATOR = "::"


@dataclass(frozen=True, slots=True)
class SpeechVoice:
    """A model-bound voice choice exposed by the native TTS picker."""

    model: str
    voice_id: str
    language: str

    @property
    def selection_id(self) -> str:
        """Return a stable Home Assistant voice ID that includes its model."""
        return f"{self.model}{VOICE_ID_SEPARATOR}{self.voice_id}"

    @property
    def name(self) -> str:
        """Return a voice label that keeps the model visible in the picker."""
        voice_name = self.voice_id.partition("_")[2].replace("_", " ").title()
        return f"{self.model} — {voice_name}"

    def name_for_language(self, language: str) -> str:
        """Return a picker label, disambiguating broad English selections."""
        voice_name = self.name
        if language.strip().replace("_", "-").casefold() == "en":
            if self.language == "en-US":
                voice_name += " (American English)"
            elif self.language == "en-GB":
                voice_name += " (British English)"
        return voice_name


def parse_voice_selection(value: Any) -> tuple[str, str] | None:
    """Parse a model-bound voice ID, returning ``(model, native_voice)``."""
    if not isinstance(value, str):
        return None
    model, separator, voice_id = value.rpartition(VOICE_ID_SEPARATOR)
    if not separator or not model.strip() or not voice_id.strip():
        return None
    return model, voice_id


def has_voice_selection_marker(value: Any) -> bool:
    """Return true when a value is intended to be a model-bound voice ID."""
    return isinstance(value, str) and VOICE_ID_SEPARATOR in value


def _is_kokoro_model(model: Any) -> bool:
    """Return true when a runtime model is the supported Kokoro backend."""
    model_id = getattr(getattr(model, "id", None), "value", None)
    if not isinstance(model_id, str):
        model_id = model if isinstance(model, str) else None
    recipe = getattr(model, "recipe", None)
    if isinstance(recipe, str) and recipe.casefold() in {"kokoro", "kokoro-tts"}:
        return True
    return isinstance(model_id, str) and model_id.casefold() in {
        "kokoro",
        "kokoro-v1",
    }


def _model_id(model: Any) -> str | None:
    """Return a runtime model's string ID."""
    model_id = getattr(getattr(model, "id", None), "value", None)
    if isinstance(model_id, str) and model_id.strip():
        return model_id.strip()
    if isinstance(model, str) and model.strip():
        return model.strip()
    return None


def _primary_language(language: str) -> str:
    """Return a case-insensitive primary language component."""
    return language.partition("-")[0].casefold().replace("_", "-")


def language_matches(requested: Any, voice_language: str) -> bool:
    """Return whether a Home Assistant language selects a voice language."""
    if not isinstance(requested, str) or not requested.strip():
        return False
    requested_normalized = requested.strip().replace("_", "-").casefold()
    voice_normalized = voice_language.casefold()
    if requested_normalized == voice_normalized:
        return True
    # A primary tag (for example ``en``) intentionally covers both regional
    # English voice groups. Other primary tags select their one Kokoro family.
    return "-" not in requested_normalized and (
        _primary_language(requested_normalized) == _primary_language(voice_normalized)
    )


def _iter_kokoro_models(models: Iterable[Any]) -> Iterable[str]:
    """Yield available Kokoro model IDs once, preserving catalog order."""
    seen: set[str] = set()
    for model in models:
        if not _is_kokoro_model(model):
            continue
        model_id = _model_id(model)
        if model_id is not None and model_id not in seen:
            seen.add(model_id)
            yield model_id


def speech_voice_catalog(models: Iterable[Any]) -> tuple[SpeechVoice, ...]:
    """Build model-bound Kokoro voices from downloaded runtime models.

    OpenMOSS voices are deliberately absent until Lemonade exposes a stable
    saved-voice discovery contract. This function therefore never invents a
    Home Assistant-owned voice library or assumes an OpenMOSS voice ID.
    """
    voices: list[SpeechVoice] = []
    for model_id in _iter_kokoro_models(models):
        voices.extend(
            SpeechVoice(model_id, voice_id, language)
            for voice_id, language in _KOKORO_VOICE_DEFINITIONS
        )
    return tuple(voices)


def supported_languages(models: Iterable[Any]) -> list[str]:
    """Return native picker languages for the currently available voices."""
    voices = speech_voice_catalog(models)
    return [
        language
        for language in KOKORO_SUPPORTED_LANGUAGES
        if any(language_matches(language, voice.language) for voice in voices)
    ]


def voices_for_language(
    models: Iterable[Any], language: str
) -> tuple[SpeechVoice, ...]:
    """Return model-bound voices compatible with one selected language."""
    return tuple(
        voice
        for voice in speech_voice_catalog(models)
        if language_matches(language, voice.language)
    )


def find_voice(
    models: Iterable[Any], model_id: str, voice_id: str
) -> SpeechVoice | None:
    """Find an available model-bound native voice by exact identity."""
    return next(
        (
            voice
            for voice in speech_voice_catalog(models)
            if voice.model == model_id and voice.voice_id == voice_id
        ),
        None,
    )
