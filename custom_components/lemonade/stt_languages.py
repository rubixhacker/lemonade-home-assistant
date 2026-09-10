"""Language support for Lemonade speech-to-text models."""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.generated.languages import LANGUAGES


# Whisper.cpp's multilingual models expose the 99 language tokens below.  The
# API takes the ISO-639-1 token, while Home Assistant may present a regional or
# script-qualified BCP-47 locale (for example, ``pt-BR`` or ``zh-Hant``).
WHISPER_LANGUAGE_CODES = frozenset(
    {
        "af",
        "am",
        "ar",
        "as",
        "az",
        "ba",
        "be",
        "bg",
        "bn",
        "bo",
        "br",
        "bs",
        "ca",
        "cs",
        "cy",
        "da",
        "de",
        "el",
        "en",
        "es",
        "et",
        "eu",
        "fa",
        "fi",
        "fo",
        "fr",
        "gl",
        "gu",
        "ha",
        "haw",
        "he",
        "hi",
        "hr",
        "ht",
        "hu",
        "hy",
        "id",
        "is",
        "it",
        "ja",
        "jw",
        "ka",
        "kk",
        "km",
        "kn",
        "ko",
        "la",
        "lb",
        "ln",
        "lo",
        "lt",
        "lv",
        "mg",
        "mi",
        "mk",
        "ml",
        "mn",
        "mr",
        "ms",
        "mt",
        "my",
        "ne",
        "nl",
        "nn",
        "no",
        "oc",
        "pa",
        "pl",
        "ps",
        "pt",
        "ro",
        "ru",
        "sa",
        "sd",
        "si",
        "sk",
        "sl",
        "sn",
        "so",
        "sq",
        "sr",
        "su",
        "sv",
        "sw",
        "ta",
        "te",
        "tg",
        "th",
        "tk",
        "tl",
        "tr",
        "tt",
        "uk",
        "ur",
        "uz",
        "vi",
        "yi",
        "yo",
        "zh",
    }
)

# These are the Whisper models currently in Lemonade's built-in catalog. The
# catalog's ``recipe`` identifies the backend, but does not include checkpoint
# metadata, so a custom ``whispercpp`` record is not treated as multilingual
# solely from its recipe. See Lemonade's catalog and the upstream model naming
# contract:
# https://raw.githubusercontent.com/lemonade-sdk/lemonade/main/src/cpp/resources/server_models.json
# https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md
_KNOWN_MULTILINGUAL_WHISPER_MODELS = frozenset(
    {
        "whisper-tiny",
        "whisper-base",
        "whisper-small",
        "whisper-medium",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
    }
)

_WHISPER_ENGLISH_ONLY_SUFFIX = re.compile(r"\.en(?:[-.]|$)", re.IGNORECASE)


def language_code(locale: Any) -> str | None:
    """Return the base ISO language code from a Home Assistant locale."""
    if not isinstance(locale, str):
        return None
    value = locale.strip().replace("_", "-").lower()
    if not value:
        return None
    return value.partition("-")[0]


def model_language_codes(model: Any) -> frozenset[str] | None:
    """Return known backend language codes, or None when the backend is unknown.

    ``whispercpp`` follows whisper.cpp's model naming contract for Lemonade's
    current built-in models: models whose name contains ``.en`` are
    English-only and the listed built-ins are multilingual. Lemonade's current
    Moonshine streaming checkpoints are English-only. Other recipes and
    unrecognized custom models are intentionally left unknown because the
    model catalog does not carry a language capability field. The current
    Lemonade catalog has no FLM transcription models; an FLM model added later
    needs an explicit language contract before it can be offered here.
    """
    recipe = getattr(model, "recipe", "")
    if not isinstance(recipe, str):
        return None
    recipe = recipe.strip().lower()
    if recipe == "moonshine":
        # Lemonade documents the current Moonshine streaming checkpoints as
        # English-only and says the request language is accepted but ignored:
        # https://lemonade-server.ai/docs/guide/configuration/moonshine/
        return frozenset({"en"})
    if recipe != "whispercpp":
        return None

    model_id = str(getattr(model, "id", ""))
    normalized_id = model_id.strip().lower()
    bare_model_id = normalized_id.removeprefix("builtin.")
    if bare_model_id in _KNOWN_MULTILINGUAL_WHISPER_MODELS:
        return WHISPER_LANGUAGE_CODES
    # Preserve the upstream ``.en`` convention for explicitly named Whisper
    # variants while avoiding claims about arbitrary custom checkpoints.
    if bare_model_id.startswith("whisper-") and _WHISPER_ENGLISH_ONLY_SUFFIX.search(
        bare_model_id
    ):
        return frozenset({"en"})
    return None


def supported_model_languages(
    model: Any,
    languages: Iterable[str] = LANGUAGES,
) -> list[str]:
    """Return Home Assistant locales supported by a known STT model."""
    codes = model_language_codes(model)
    if codes is None:
        return []
    return sorted(
        (
            locale
            for locale in languages
            if isinstance(locale, str) and language_code(locale) in codes
        ),
        key=lambda locale: (locale.casefold(), locale),
    )


def require_model_language(
    model: Any,
    language: Any,
    languages: Iterable[str] = LANGUAGES,
) -> str:
    """Validate an explicit HA locale and return Lemonade's ISO language code."""
    model_id = str(getattr(model, "id", "unknown"))
    codes = model_language_codes(model)
    if codes is None:
        raise HomeAssistantError(
            f"Lemonade STT model {model_id} does not advertise supported languages"
        )

    code = language_code(language)
    if code is None:
        raise HomeAssistantError("Speech-to-text language must be selected explicitly")

    supported = supported_model_languages(model, languages)
    if not any(language_code(locale) == code for locale in supported):
        raise HomeAssistantError(
            f"Language {language!r} is not supported by Lemonade STT model {model_id}"
        )
    return code
