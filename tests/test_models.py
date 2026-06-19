"""Tests for Lemonade model parsing."""

import sys
from types import ModuleType, SimpleNamespace
import unittest


def _install_homeassistant_stubs() -> None:
    """Install minimal Home Assistant dependency stubs for unit tests."""
    aiohttp = ModuleType("aiohttp")
    aiohttp.ClientError = type("ClientError", (Exception,), {})
    aiohttp.ClientSession = type("ClientSession", (), {})
    aiohttp.FormData = type("FormData", (), {"add_field": lambda self, *args, **kwargs: None})
    sys.modules.setdefault("aiohttp", aiohttp)

    voluptuous = ModuleType("voluptuous")
    voluptuous.Optional = lambda key, *args, **kwargs: key
    voluptuous.Required = lambda key, *args, **kwargs: key
    voluptuous.Schema = lambda schema, *args, **kwargs: schema
    voluptuous.Coerce = lambda value_type: value_type
    sys.modules.setdefault("voluptuous", voluptuous)

    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules.setdefault("homeassistant", homeassistant)

    config_entries = ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    sys.modules.setdefault("homeassistant.config_entries", config_entries)

    const = ModuleType("homeassistant.const")
    const.CONF_API_KEY = "api_key"
    const.CONF_MODEL = "model"
    const.CONF_URL = "url"
    const.Platform = SimpleNamespace(
        SENSOR="sensor",
        SELECT="select",
        CONVERSATION="conversation",
        AI_TASK="ai_task",
        TTS="tts",
        STT="stt",
    )
    sys.modules.setdefault("homeassistant.const", const)

    core = ModuleType("homeassistant.core")
    core.HomeAssistant = type("HomeAssistant", (), {})
    core.ServiceCall = type("ServiceCall", (), {})
    core.SupportsResponse = SimpleNamespace(OPTIONAL="optional")
    sys.modules.setdefault("homeassistant.core", core)

    exceptions = ModuleType("homeassistant.exceptions")
    exceptions.ConfigEntryAuthFailed = type("ConfigEntryAuthFailed", (Exception,), {})
    exceptions.ConfigEntryError = type("ConfigEntryError", (Exception,), {})
    exceptions.ConfigEntryNotReady = type("ConfigEntryNotReady", (Exception,), {})
    exceptions.HomeAssistantError = type("HomeAssistantError", (Exception,), {})
    sys.modules.setdefault("homeassistant.exceptions", exceptions)

    helpers = ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    sys.modules.setdefault("homeassistant.helpers", helpers)

    config_validation = ModuleType("homeassistant.helpers.config_validation")
    config_validation.config_entry_only_config_schema = lambda domain: None
    config_validation.string = str
    sys.modules.setdefault(
        "homeassistant.helpers.config_validation",
        config_validation,
    )
    helpers.config_validation = config_validation

    aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = lambda hass: None
    sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client)

    typing = ModuleType("homeassistant.helpers.typing")
    typing.ConfigType = dict
    sys.modules.setdefault("homeassistant.helpers.typing", typing)


_install_homeassistant_stubs()

from lemonade.const import (  # noqa: E402
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CAPABILITY_EMBEDDINGS,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_STT,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_TTS,
    CAPABILITY_VISION,
)
from lemonade.models import parse_models_response  # noqa: E402


SAMPLE_MODELS = [
    {"id": "Bonsai-8B-gguf", "recipe": "llamacpp", "labels": []},
    {"id": "Qwen3.6-27B-GGUF", "recipe": "llamacpp", "labels": ["vision"]},
    {
        "id": "Flux-2-Klein-9B-GGUF",
        "recipe": "diffusers",
        "labels": ["image", "image_edit"],
    },
    {"id": "kokoro-v1", "recipe": "tts", "labels": ["tts"]},
    {"id": "future-stt", "recipe": "stt", "labels": ["speech-to-text"]},
    {
        "id": "Qwen3-Embedding-0.6B-GGUF",
        "recipe": "embedding",
        "labels": ["embeddings"],
    },
    {
        "id": "not-downloaded",
        "recipe": "llamacpp",
        "labels": [],
        "downloaded": False,
    },
]


class ParseModelsResponseTest(unittest.TestCase):
    def test_maps_downloaded_models_to_capabilities(self) -> None:
        catalog = parse_models_response({"data": SAMPLE_MODELS})

        self.assertEqual(
            ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"],
            catalog.model_ids(CAPABILITY_CONVERSATION),
        )
        self.assertEqual(
            ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"],
            catalog.model_ids(CAPABILITY_AI_TASK),
        )
        self.assertEqual(
            ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"],
            catalog.model_ids(CAPABILITY_TOOL_CALLING),
        )
        self.assertEqual(
            ["Qwen3.6-27B-GGUF"],
            catalog.model_ids(CAPABILITY_VISION),
        )
        self.assertEqual(
            ["Flux-2-Klein-9B-GGUF"],
            catalog.model_ids(CAPABILITY_IMAGE),
        )
        self.assertEqual(
            ["Flux-2-Klein-9B-GGUF"],
            catalog.model_ids(CAPABILITY_IMAGE_EDIT),
        )
        self.assertEqual(["kokoro-v1"], catalog.model_ids(CAPABILITY_TTS))
        self.assertEqual(["future-stt"], catalog.model_ids(CAPABILITY_STT))
        self.assertEqual(
            ["Qwen3-Embedding-0.6B-GGUF"],
            catalog.model_ids(CAPABILITY_EMBEDDINGS),
        )
        self.assertNotIn("not-downloaded", catalog.all_model_ids)


if __name__ == "__main__":
    unittest.main()
