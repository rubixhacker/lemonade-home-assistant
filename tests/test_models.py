"""Tests for Lemonade model parsing."""

from pathlib import Path
import sys
from types import MappingProxyType, ModuleType, SimpleNamespace
from typing import Any
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))


class _VolMarker:
    def __init__(
        self,
        key: str,
        *args: Any,
        default: Any = None,
        description: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.key = key
        self.default = default
        self.description = description

    def __hash__(self) -> int:
        return id(self)


class _VolSchema:
    def __init__(self, schema: dict[Any, Any], *args: Any, **kwargs: Any) -> None:
        self.schema = schema


class _FlowBase:
    def async_show_form(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "create_entry", **kwargs}

    def async_abort(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "abort", **kwargs}

    def add_suggested_values_to_schema(
        self, schema: Any, suggested_values: dict[str, Any]
    ) -> Any:
        return schema


class _ConfigFlowBase(_FlowBase):
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()

    async def async_set_unique_id(self, unique_id: str) -> None:
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self) -> None:
        return None

    def _async_current_entries(self) -> list[Any]:
        return getattr(self, "_current_entries", [])

    def _get_reconfigure_entry(self) -> Any:
        return self._reconfigure_entry


class _ConfigSubentryFlowBase(_FlowBase):
    def _get_entry(self) -> Any:
        return self._flow_entry

    def _get_reconfigure_subentry(self) -> Any:
        return self._reconfigure_subentry_obj

    def async_update_and_abort(
        self,
        config_entry: Any,
        subentry: Any,
        *,
        data: dict[str, Any],
        title: str | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "abort",
            "reason": "reconfigure_successful",
            "entry": config_entry,
            "subentry": subentry,
            "data": data,
            "title": title,
        }


def _install_homeassistant_stubs() -> None:
    """Install minimal Home Assistant dependency stubs for unit tests."""
    aiohttp = ModuleType("aiohttp")
    aiohttp.ClientError = type("ClientError", (Exception,), {})
    aiohttp.ClientSession = type("ClientSession", (), {})
    aiohttp.ClientTimeout = type(
        "ClientTimeout", (), {"__init__": lambda self, total=None, **kwargs: setattr(self, "total", total)}
    )
    aiohttp.FormData = type("FormData", (), {"add_field": lambda self, *args, **kwargs: None})
    sys.modules.setdefault("aiohttp", aiohttp)

    voluptuous = ModuleType("voluptuous")
    voluptuous.Optional = lambda key, *args, **kwargs: _VolMarker(
        key, *args, **kwargs
    )
    voluptuous.Required = lambda key, *args, **kwargs: _VolMarker(
        key, *args, **kwargs
    )
    voluptuous.Schema = _VolSchema
    voluptuous.Coerce = lambda value_type: value_type
    voluptuous.All = lambda *validators: validators
    voluptuous.Range = lambda **kwargs: lambda value: value
    sys.modules.setdefault("voluptuous", voluptuous)

    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules.setdefault("homeassistant", homeassistant)

    config_entries = ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = type(
        "ConfigEntry",
        (),
        {"__class_getitem__": classmethod(lambda cls, item: cls)},
    )
    config_entries.ConfigEntryState = SimpleNamespace(LOADED="loaded")
    config_entries.ConfigFlow = _ConfigFlowBase
    config_entries.OptionsFlow = _FlowBase
    config_entries.ConfigSubentryFlow = _ConfigSubentryFlowBase

    class ConfigSubentry:
        def __init__(
            self,
            *,
            data: dict[str, Any],
            subentry_type: str,
            title: str,
            unique_id: str | None,
        ) -> None:
            self.data = MappingProxyType(data)
            self.subentry_id = "starter-conversation"
            self.subentry_type = subentry_type
            self.title = title
            self.unique_id = unique_id

    config_entries.ConfigSubentry = ConfigSubentry
    sys.modules.setdefault("homeassistant.config_entries", config_entries)

    const = ModuleType("homeassistant.const")
    const.CONF_API_KEY = "api_key"
    const.CONF_MODEL = "model"
    const.CONF_NAME = "name"
    const.CONF_PROMPT = "prompt"
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
    core.callback = lambda func: func
    core.SupportsResponse = SimpleNamespace(OPTIONAL="optional")
    sys.modules.setdefault("homeassistant.core", core)

    data_entry_flow = ModuleType("homeassistant.data_entry_flow")
    data_entry_flow.FlowResult = dict
    sys.modules.setdefault("homeassistant.data_entry_flow", data_entry_flow)

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
    config_validation.boolean = bool
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
    CAPABILITY_CLASSIFICATION,
    CAPABILITY_CONVERSATION,
    CAPABILITY_EMBEDDINGS,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_STT,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_TTS,
    CAPABILITY_VISION,
)
import lemonade.models as lemonade_models  # noqa: E402
from lemonade.server_capabilities import RuntimeCapabilityView  # noqa: E402
from lemonade.models import parse_models_response  # noqa: E402


SAMPLE_MODELS = [
    {"id": "Bonsai-8B-gguf", "recipe": "llamacpp", "labels": ["tool-calling"]},
    {"id": "Qwen3.6-27B-GGUF", "recipe": "llamacpp", "labels": ["vision"]},
    {
        "id": "Flux-2-Klein-9B-GGUF",
        "recipe": "diffusers",
        "labels": ["image", "edit"],
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
    def test_capability_is_closed_and_string_compatible(self) -> None:
        self.assertTrue(hasattr(lemonade_models, "Capability"))
        Capability = lemonade_models.Capability

        self.assertIsInstance(Capability.CONVERSATION, str)
        self.assertEqual(CAPABILITY_CONVERSATION, Capability.CONVERSATION)

        with self.assertRaises(ValueError):
            Capability("not_a_capability")

    def test_model_id_rejects_blank_values_at_boundary(self) -> None:
        self.assertTrue(hasattr(lemonade_models, "ModelId"))
        ModelId = lemonade_models.ModelId

        with self.assertRaises(ValueError):
            ModelId("")
        with self.assertRaises(ValueError):
            ModelId("   ")

        self.assertIsNone(ModelId.parse(""))
        self.assertIsNone(ModelId.parse("   "))
        self.assertEqual(ModelId("chat-model"), ModelId.parse(" chat-model "))

    def test_catalog_keeps_typed_model_ids_internal_and_strings_external(self) -> None:
        self.assertTrue(hasattr(lemonade_models, "Capability"))
        self.assertTrue(hasattr(lemonade_models, "ModelId"))
        Capability = lemonade_models.Capability
        ModelId = lemonade_models.ModelId

        catalog = parse_models_response(
            {
                "data": [
                    {
                        "id": " chat-model ",
                        "recipe": "llamacpp",
                        "labels": [],
                    }
                ]
            }
        )

        self.assertEqual(ModelId("chat-model"), catalog.models[0].id)
        self.assertEqual(["chat-model"], catalog.all_model_ids)
        self.assertEqual(["chat-model"], catalog.model_ids(Capability.CONVERSATION))
        self.assertEqual("chat-model", catalog.first_model_id(Capability.CONVERSATION))

    def test_server_capability_view_accepts_typed_and_legacy_capabilities(self) -> None:
        self.assertTrue(hasattr(lemonade_models, "Capability"))
        Capability = lemonade_models.Capability

        catalog = parse_models_response({"data": SAMPLE_MODELS})

        self.assertEqual(
            ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"],
            catalog.model_ids(Capability.CONVERSATION),
        )
        self.assertEqual(
            "Bonsai-8B-gguf",
            RuntimeCapabilityView(catalog).resolve_model(Capability.CONVERSATION),
        )
        self.assertEqual(
            ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"],
            catalog.model_ids(CAPABILITY_CONVERSATION),
        )

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
            ["Bonsai-8B-gguf"],
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

    def test_chat_collections_are_explicit_profile_choices_not_fallbacks(self) -> None:
        catalog = parse_models_response(
            {
                "data": [
                    {"id": "ordinary-chat", "recipe": "llamacpp"},
                    {
                        "id": "router-policy",
                        "recipe": "router",
                        "labels": ["tool-calling"],
                    },
                    {
                        "id": "omni-orchestrator",
                        "recipe": "omni",
                        "labels": ["image", "tts"],
                    },
                    {
                        "id": "image-task",
                        "recipe": "diffusers",
                        "labels": ["image"],
                    },
                    {
                        "id": "not-downloaded-router",
                        "recipe": "router",
                        "downloaded": False,
                    },
                ]
            }
        )

        for capability in (CAPABILITY_CONVERSATION, CAPABILITY_AI_TASK):
            with self.subTest(capability=capability):
                self.assertEqual(["ordinary-chat"], catalog.model_ids(capability))
                self.assertEqual("ordinary-chat", catalog.first_model_id(capability))
                self.assertEqual(
                    [
                        "ordinary-chat",
                        "router-policy",
                        "omni-orchestrator",
                        "image-task",
                    ],
                    catalog.profile_model_ids(capability),
                )

        self.assertEqual(["image-task"], catalog.model_ids(CAPABILITY_IMAGE))
        self.assertEqual([], catalog.model_ids(CAPABILITY_TTS))
        self.assertEqual([], catalog.model_ids(CAPABILITY_TOOL_CALLING))

        self.assertNotIn(
            "not-downloaded-router",
            catalog.profile_model_ids(CAPABILITY_CONVERSATION),
        )

    def test_discovers_text_classification_models_from_advertised_labels(self) -> None:
        catalog = parse_models_response(
            {
                "data": [
                    {
                        "id": "classifier-first",
                        "recipe": "encoder",
                        "labels": ["classification"],
                    },
                    {
                        "id": "classifier-second",
                        "recipe": "encoder",
                        "labels": ["text-classification"],
                    },
                ]
            }
        )

        self.assertEqual(
            ["classifier-first", "classifier-second"],
            catalog.model_ids(CAPABILITY_CLASSIFICATION),
        )
        self.assertEqual(
            "classifier-first", catalog.first_model_id(CAPABILITY_CLASSIFICATION)
        )

    def test_tool_calling_accepts_label_aliases(self) -> None:
        catalog = parse_models_response(
            {
                "data": [
                    {"id": "plain-llm", "recipe": "llamacpp", "labels": []},
                    {
                        "id": "underscore-llm",
                        "recipe": "llamacpp",
                        "labels": ["tool_calling"],
                    },
                    {
                        "id": "tool-llm",
                        "recipe": "llamacpp",
                        "labels": ["tool-calling"],
                    },
                ]
            }
        )

        self.assertEqual(
            ["underscore-llm", "tool-llm"],
            catalog.model_ids(CAPABILITY_TOOL_CALLING),
        )

    def test_reranking_models_are_not_classified_as_chat(self) -> None:
        """Lemonade 11.9 reserved-directory models are non-chat models."""
        catalog = parse_models_response(
            {
                "data": [
                    {
                        "id": "extra.reranker-Q4_K_M",
                        "recipe": "llamacpp",
                        "labels": ["custom", "reranking"],
                    },
                    {
                        "id": "extra.embedding-model",
                        "recipe": "llamacpp",
                        "labels": ["embeddings"],
                    },
                    {
                        "id": "extra.chat-model",
                        "recipe": "llamacpp",
                        "labels": ["chat"],
                    },
                ]
            }
        )

        self.assertEqual(
            ["extra.embedding-model"],
            catalog.model_ids(CAPABILITY_EMBEDDINGS),
        )
        self.assertEqual(
            ["extra.chat-model"],
            catalog.model_ids(CAPABILITY_CONVERSATION),
        )

    def test_legacy_extra_ids_remain_parseable_saved_model_values(self) -> None:
        """11.9 hides old folder aliases, but persisted IDs remain opaque values."""
        catalog = parse_models_response(
            {
                "data": [
                    {
                        "id": "extra.chat",
                        "recipe": "llamacpp",
                        "labels": ["chat"],
                    },
                    {
                        "id": "extra.embeddings",
                        "recipe": "llamacpp",
                        "labels": ["embeddings"],
                    },
                    {
                        "id": "extra.reranking",
                        "recipe": "llamacpp",
                        "labels": ["reranking"],
                    },
                ]
            }
        )

        self.assertEqual(
            ["extra.chat"], catalog.model_ids(CAPABILITY_CONVERSATION)
        )
        self.assertEqual(
            ["extra.embeddings"], catalog.model_ids(CAPABILITY_EMBEDDINGS)
        )
        self.assertNotIn("extra.reranking", catalog.model_ids(CAPABILITY_CONVERSATION))

    def test_image_edit_accepts_edit_label(self) -> None:
        catalog = parse_models_response(
            {
                "data": [
                    {
                        "id": "edit-image-model",
                        "recipe": "diffusers",
                        "labels": ["edit"],
                    }
                ]
            }
        )

        self.assertEqual(
            ["edit-image-model"],
            catalog.model_ids(CAPABILITY_IMAGE_EDIT),
        )

    def test_models_for_returns_tuple(self) -> None:
        catalog = parse_models_response({"data": SAMPLE_MODELS})

        self.assertIsInstance(catalog.models_for(CAPABILITY_CONVERSATION), tuple)


if __name__ == "__main__":
    unittest.main()
