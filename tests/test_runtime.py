"""Tests for Lemonade runtime setup."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import Any
import unittest


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


class _OptionsFlowBase(_FlowBase):
    pass


class _ConfigSubentryFlowBase(_FlowBase):
    def async_update_and_abort(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "type": "abort",
            "reason": "reconfigure_successful",
            "args": args,
            **kwargs,
        }


class _SelectSelectorConfig:
    def __init__(
        self,
        *,
        options: list[str] | None = None,
        multiple: bool = False,
        mode: str | None = None,
    ) -> None:
        self.options = options or []
        self.multiple = multiple
        self.mode = mode


class _SelectSelector:
    def __init__(self, config: _SelectSelectorConfig) -> None:
        self.config = config


class _TemplateSelector:
    pass


def _install_homeassistant_stubs() -> None:
    """Install minimal Home Assistant dependency stubs for unit tests."""
    aiohttp = ModuleType("aiohttp")
    aiohttp.ClientError = type("ClientError", (Exception,), {})
    aiohttp.ClientSession = type("ClientSession", (), {})
    aiohttp.FormData = type(
        "FormData", (), {"add_field": lambda self, *args, **kwargs: None}
    )
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
    voluptuous.Invalid = type("Invalid", (Exception,), {})
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
    config_entries.OptionsFlow = _OptionsFlowBase
    config_entries.ConfigSubentryFlow = _ConfigSubentryFlowBase
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
    sys.modules.setdefault(
        "homeassistant.helpers.config_validation",
        config_validation,
    )
    helpers.config_validation = config_validation

    aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = lambda hass: "session"
    sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client)

    llm = ModuleType("homeassistant.helpers.llm")
    llm.async_get_apis = lambda hass: getattr(hass, "llm_apis", [])
    sys.modules.setdefault("homeassistant.helpers.llm", llm)
    helpers.llm = llm

    selector = ModuleType("homeassistant.helpers.selector")
    selector.SelectSelector = _SelectSelector
    selector.SelectSelectorConfig = _SelectSelectorConfig
    selector.TemplateSelector = _TemplateSelector
    sys.modules.setdefault("homeassistant.helpers.selector", selector)

    issue_registry = ModuleType("homeassistant.helpers.issue_registry")
    issue_registry.CREATED = []
    issue_registry.DELETED = []
    issue_registry.IssueSeverity = SimpleNamespace(WARNING="warning")

    def async_create_issue(*args: Any, **kwargs: Any) -> None:
        issue_registry.CREATED.append((args, kwargs))

    def async_delete_issue(*args: Any, **kwargs: Any) -> None:
        issue_registry.DELETED.append((args, kwargs))

    issue_registry.async_create_issue = async_create_issue
    issue_registry.async_delete_issue = async_delete_issue
    sys.modules.setdefault("homeassistant.helpers.issue_registry", issue_registry)

    update_coordinator = ModuleType("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        def __init__(self, hass: Any, logger: Any, **kwargs: Any) -> None:
            self.hass = hass
            self.logger = logger
            self.name = kwargs.get("name")
            self.config_entry = kwargs.get("config_entry")
            self.update_interval = kwargs.get("update_interval")
            self.data = None
            self.listeners = []

        @classmethod
        def __class_getitem__(cls, item: Any) -> type["DataUpdateCoordinator"]:
            return cls

        async def async_config_entry_first_refresh(self) -> None:
            self.data = await self._async_update_data()

        def async_add_listener(self, update_callback: Any) -> Any:
            self.listeners.append(update_callback)
            return lambda: self.listeners.remove(update_callback)

    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    sys.modules.setdefault("homeassistant.helpers.update_coordinator", update_coordinator)

    typing = ModuleType("homeassistant.helpers.typing")
    typing.ConfigType = dict
    sys.modules.setdefault("homeassistant.helpers.typing", typing)


_install_homeassistant_stubs()

from homeassistant.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_MODEL,
    CONF_NAME,
    CONF_PROMPT,
    CONF_URL,
)
from homeassistant.helpers import issue_registry as ir  # noqa: E402

import lemonade as integration  # noqa: E402
from lemonade.api import LemonadeClient  # noqa: E402
from lemonade.const import (  # noqa: E402
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_DEFAULT_AI_TASK_MODEL,
    CONF_DEFAULT_CONVERSATION_MODEL,
    CONF_DEFAULT_IMAGE_MODEL,
    CONF_DEFAULT_STT_MODEL,
    CONF_DEFAULT_TTS_MODEL,
    CONF_LLM_HASS_API,
    CONF_TIMEOUT,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    PLATFORMS,
    SUBENTRY_TYPE_AI_TASK,
    SUBENTRY_TYPE_CONVERSATION,
)
from lemonade.data import LemonadeRuntimeData  # noqa: E402


class FakeConfigEntries:
    def __init__(self) -> None:
        self.forwarded: list[tuple[Any, Any]] = []
        self.unloaded: list[tuple[Any, Any]] = []

    async def async_forward_entry_setups(self, entry: Any, platforms: Any) -> None:
        self.forwarded.append((entry, platforms))

    async def async_unload_platforms(self, entry: Any, platforms: Any) -> bool:
        self.unloaded.append((entry, platforms))
        return True

    async def async_reload(self, entry_id: str) -> None:
        self.reloaded = entry_id


class FakeHass:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.config_entries = FakeConfigEntries()


class FakeEntry:
    entry_id = "entry-1"
    state = "loaded"
    data = {
        CONF_URL: "http://lemonade.local",
        CONF_API_KEY: "secret",
        CONF_TIMEOUT: 12.0,
    }
    options: dict[str, Any] = {}

    def __init__(self) -> None:
        self.runtime_data = None
        self.unloads: list[Any] = []
        self.update_listener = None

    def add_update_listener(self, listener: Any) -> Any:
        self.update_listener = listener
        return lambda: None

    def async_on_unload(self, unload: Any) -> None:
        self.unloads.append(unload)


class FakeResponse:
    status = 200
    headers: dict[str, str] = {}

    def __init__(self, payload: Any) -> None:
        self.payload = payload

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def json(self, *args: Any, **kwargs: Any) -> Any:
        return self.payload

    async def text(self) -> str:
        return ""


class FakeSession:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.requests: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append((method, url, kwargs))
        return FakeResponse(self.payload)


def _schema_fields(data_schema: Any) -> dict[str, tuple[Any, Any]]:
    schema = getattr(data_schema, "schema", data_schema)
    return {getattr(key, "key", key): (key, value) for key, value in schema.items()}


class FakeCatalog:
    def __init__(self, model_ids: dict[str, list[str]]) -> None:
        self._model_ids = model_ids

    def model_ids(self, capability: str) -> list[str]:
        return list(self._model_ids.get(capability, []))


class RuntimeSetupTest(unittest.IsolatedAsyncioTestCase):

    def test_config_flow_registers_profile_subentry_types(self) -> None:
        from lemonade.config_flow import (
            LemonadeConfigFlow,
            LemonadeProfileSubentryFlow,
        )

        supported = LemonadeConfigFlow.async_get_supported_subentry_types(FakeEntry())

        self.assertEqual(
            {
                SUBENTRY_TYPE_CONVERSATION: LemonadeProfileSubentryFlow,
                SUBENTRY_TYPE_AI_TASK: LemonadeProfileSubentryFlow,
            },
            supported,
        )

    async def test_ai_task_profile_subentry_flow_uses_ai_task_models(self) -> None:
        from lemonade.config_flow import LemonadeProfileSubentryFlow

        entry = SimpleNamespace(
            state="loaded",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog(
                        {
                            CAPABILITY_CONVERSATION: ["chat-a"],
                            CAPABILITY_AI_TASK: ["task-a"],
                        }
                    )
                )
            ),
        )
        flow = LemonadeProfileSubentryFlow(entry, SUBENTRY_TYPE_AI_TASK)
        flow.hass = SimpleNamespace(
            llm_apis=[{"value": "assist", "label": "Assist"}]
        )

        result = await flow.async_step_user()

        self.assertEqual("form", result["type"])
        fields = _schema_fields(result["data_schema"])
        self.assertEqual(["task-a"], fields[CONF_MODEL][1].config.options)
        self.assertNotIn(CONF_LLM_HASS_API, fields)

    async def test_conversation_profile_subentry_flow_builds_schema(self) -> None:
        from lemonade.config_flow import LemonadeProfileSubentryFlow

        entry = SimpleNamespace(
            state="loaded",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog(
                        {CAPABILITY_CONVERSATION: ["chat-a", "chat-b"]}
                    )
                )
            ),
        )
        flow = LemonadeProfileSubentryFlow(entry, SUBENTRY_TYPE_CONVERSATION)
        flow.hass = SimpleNamespace(
            llm_apis=[{"value": "assist", "label": "Assist"}]
        )

        result = await flow.async_step_user()

        self.assertEqual("form", result["type"])
        fields = _schema_fields(result["data_schema"])
        self.assertIs(fields[CONF_NAME][1], str)
        self.assertEqual(["chat-a", "chat-b"], fields[CONF_MODEL][1].config.options)
        self.assertIsInstance(fields[CONF_PROMPT][1], _TemplateSelector)
        self.assertEqual(
            [{"value": "assist", "label": "Assist"}],
            fields[CONF_LLM_HASS_API][1].config.options,
        )
        self.assertTrue(fields[CONF_LLM_HASS_API][1].config.multiple)

    async def test_profile_subentry_flow_reconfigures_existing_profile(self) -> None:
        from lemonade.config_flow import LemonadeProfileSubentryFlow

        subentry = SimpleNamespace(
            data={
                CONF_NAME: "Old profile",
                CONF_MODEL: "chat-b",
                CONF_PROMPT: "Old prompt",
                CONF_LLM_HASS_API: ["assist"],
            }
        )
        entry = SimpleNamespace(
            state="loaded",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog(
                        {CAPABILITY_CONVERSATION: ["chat-a", "chat-b"]}
                    )
                )
            ),
        )
        flow = LemonadeProfileSubentryFlow(
            entry, SUBENTRY_TYPE_CONVERSATION, subentry
        )
        flow.hass = SimpleNamespace(llm_apis=[{"value": "assist", "label": "Assist"}])

        form = await flow.async_step_reconfigure()

        fields = _schema_fields(form["data_schema"])
        self.assertEqual("Old profile", fields[CONF_NAME][0].default)
        self.assertEqual("chat-b", fields[CONF_MODEL][0].default)
        self.assertEqual("Old prompt", fields[CONF_PROMPT][0].default)
        self.assertEqual(["assist"], fields[CONF_LLM_HASS_API][0].default)

        submitted = {CONF_NAME: "New profile", CONF_MODEL: "chat-a"}
        result = await flow.async_step_reconfigure(submitted)

        self.assertEqual("abort", result["type"])
        self.assertEqual("reconfigure_successful", result["reason"])
        self.assertEqual((subentry,), result["args"])
        self.assertEqual("New profile", result["title"])
        self.assertEqual(submitted, result["data"])

    async def test_options_flow_builds_schema_from_loaded_runtime_catalog(self) -> None:
        from lemonade.config_flow import LemonadeConfigFlow, LemonadeOptionsFlow

        entry = SimpleNamespace(
            data={CONF_API_KEY: "secret", CONF_TIMEOUT: 12.0},
            options={
                CONF_TIMEOUT: 8.0,
                CONF_DEFAULT_CONVERSATION_MODEL: "chat-b",
            },
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog(
                        {
                            CAPABILITY_CONVERSATION: ["chat-a", "chat-b"],
                            CAPABILITY_AI_TASK: ["task-a"],
                            CAPABILITY_IMAGE: ["image-a"],
                            CAPABILITY_TTS: ["tts-a"],
                            CAPABILITY_STT: [],
                        }
                    )
                )
            ),
        )

        flow = LemonadeConfigFlow.async_get_options_flow(entry)
        result = await flow.async_step_init()

        self.assertIsInstance(flow, LemonadeOptionsFlow)
        self.assertEqual("form", result["type"])
        fields = _schema_fields(result["data_schema"])
        self.assertEqual("secret", fields[CONF_API_KEY][0].description["suggested_value"])
        self.assertEqual(8.0, fields[CONF_TIMEOUT][0].default)
        self.assertEqual(
            ["chat-a", "chat-b"],
            fields[CONF_DEFAULT_CONVERSATION_MODEL][1].config.options,
        )
        self.assertEqual("chat-b", fields[CONF_DEFAULT_CONVERSATION_MODEL][0].default)
        self.assertEqual(["task-a"], fields[CONF_DEFAULT_AI_TASK_MODEL][1].config.options)
        self.assertEqual(["image-a"], fields[CONF_DEFAULT_IMAGE_MODEL][1].config.options)
        self.assertEqual(["tts-a"], fields[CONF_DEFAULT_TTS_MODEL][1].config.options)
        self.assertNotIn(CONF_DEFAULT_STT_MODEL, fields)

    async def test_options_flow_creates_entry_with_submitted_options(self) -> None:
        from lemonade.config_flow import LemonadeOptionsFlow

        entry = SimpleNamespace(
            data={CONF_API_KEY: "secret", CONF_TIMEOUT: 12.0},
            options={},
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(catalog=FakeCatalog({}))
            ),
        )
        submitted = {
            CONF_TIMEOUT: 9.5,
            CONF_DEFAULT_CONVERSATION_MODEL: "chat-a",
        }

        result = await LemonadeOptionsFlow(entry).async_step_init(submitted)

        self.assertEqual(
            {"type": "create_entry", "title": "", "data": submitted},
            result,
        )
        self.assertNotIn(CONF_API_KEY, result["data"])

    def setUp(self) -> None:
        ir.CREATED.clear()
        ir.DELETED.clear()

    async def test_api_models_returns_raw_list_response(self) -> None:
        client = LemonadeClient(FakeSession([{"id": "raw-model"}]), "http://server")

        models = await client.models()

        self.assertEqual([{"id": "raw-model"}], models)

    async def test_coordinator_refreshes_health_models_and_catalog(self) -> None:
        from lemonade.coordinator import LemonadeCoordinator

        class Client:
            async def health(self) -> dict[str, Any]:
                return {"status": "ok"}

            async def models(self) -> dict[str, Any]:
                return {
                    "data": [
                        {"id": "voice-model", "recipe": "tts", "labels": ["tts"]}
                    ]
                }

        coordinator = LemonadeCoordinator(FakeHass(), FakeEntry(), Client())

        data = await coordinator._async_update_data()
        coordinator.data = data

        self.assertEqual({"status": "ok"}, data["health"])
        self.assertEqual("voice-model", data["models"]["data"][0]["id"])
        self.assertEqual(["voice-model"], data["catalog"].model_ids(CAPABILITY_TTS))
        self.assertEqual({"status": "ok"}, coordinator.health)
        self.assertEqual(["voice-model"], coordinator.catalog.model_ids(CAPABILITY_TTS))
        self.assertEqual("ok", coordinator.server_status)
        self.assertEqual(
            DEFAULT_SCAN_INTERVAL_SECONDS,
            coordinator.update_interval.total_seconds(),
        )

    async def test_profile_subentry_flow_aborts_when_entry_not_loaded(self) -> None:
        from lemonade.config_flow import LemonadeProfileSubentryFlow

        entry = SimpleNamespace(
            state="not_loaded",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_CONVERSATION: ["chat-a"]})
                )
            ),
        )
        flow = LemonadeProfileSubentryFlow(entry, SUBENTRY_TYPE_CONVERSATION)

        result = await flow.async_step_user()

        self.assertEqual({"type": "abort", "reason": "entry_not_loaded"}, result)

    async def test_profile_subentry_flow_aborts_when_no_models_exist(self) -> None:
        from lemonade.config_flow import LemonadeProfileSubentryFlow

        entry = SimpleNamespace(
            state="loaded",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_CONVERSATION: []})
                )
            ),
        )
        flow = LemonadeProfileSubentryFlow(entry, SUBENTRY_TYPE_CONVERSATION)

        result = await flow.async_step_user()

        self.assertEqual({"type": "abort", "reason": "no_models"}, result)

    def test_strings_define_options_and_profile_subentry_translations(self) -> None:
        strings = json.loads(Path("lemonade/strings.json").read_text())

        self.assertIn("options", strings)
        option_data = strings["options"]["step"]["init"]["data"]
        self.assertIn(CONF_DEFAULT_CONVERSATION_MODEL, option_data)
        self.assertIn(CONF_DEFAULT_AI_TASK_MODEL, option_data)
        self.assertIn(CONF_DEFAULT_IMAGE_MODEL, option_data)
        self.assertIn(CONF_DEFAULT_TTS_MODEL, option_data)
        self.assertIn(CONF_DEFAULT_STT_MODEL, option_data)

        subentries = strings["config_subentries"]
        self.assertIn(SUBENTRY_TYPE_CONVERSATION, subentries)
        self.assertIn(SUBENTRY_TYPE_AI_TASK, subentries)
        self.assertIn(CONF_LLM_HASS_API, subentries[SUBENTRY_TYPE_CONVERSATION]["step"]["user"]["data"])
        self.assertNotIn(CONF_LLM_HASS_API, subentries[SUBENTRY_TYPE_AI_TASK]["step"]["user"]["data"])
        self.assertEqual(
            "The Lemonade Server entry is not loaded.",
            strings["config"]["abort"]["entry_not_loaded"],
        )
        self.assertEqual(
            "No compatible Lemonade models are available for this profile type.",
            strings["config"]["abort"]["no_models"],
        )

    def test_strings_define_missing_capability_repair_translation(self) -> None:
        strings = json.loads(Path("lemonade/strings.json").read_text())

        issue = strings.get("issues", {}).get("missing_capability")

        self.assertIsNotNone(issue)
        self.assertIn("{capability}", issue["title"])
        self.assertIn("{capability}", issue["description"])

    def test_repairs_create_and_delete_missing_capability_issues(self) -> None:
        from lemonade.repairs import (
            async_create_missing_capability_issue,
            async_delete_missing_capability_issue,
        )

        hass = FakeHass()

        async_create_missing_capability_issue(hass, "entry-1", CAPABILITY_IMAGE)
        async_delete_missing_capability_issue(hass, "entry-1", CAPABILITY_IMAGE)

        self.assertEqual((hass, DOMAIN, "missing_image_entry-1"), ir.CREATED[0][0])
        self.assertEqual(
            {
                "is_fixable": False,
                "severity": ir.IssueSeverity.WARNING,
                "translation_key": "missing_capability",
                "translation_placeholders": {"capability": CAPABILITY_IMAGE},
            },
            ir.CREATED[0][1],
        )
        self.assertEqual((hass, DOMAIN, "missing_image_entry-1"), ir.DELETED[0][0])

    def test_services_use_client_from_runtime_data_for_requested_entry(self) -> None:
        from homeassistant.exceptions import HomeAssistantError

        from lemonade.const import CONF_ENTRY_ID
        from lemonade.services import _get_entry_and_client

        client = LemonadeClient(FakeSession({}), "http://server")
        entry = FakeEntry()
        entry.runtime_data = LemonadeRuntimeData(client=client, coordinator=object())
        hass = SimpleNamespace(
            config_entries=SimpleNamespace(
                async_entries=lambda domain: [entry],
            ),
        )
        call = SimpleNamespace(data={CONF_ENTRY_ID: entry.entry_id})

        try:
            selected_entry, selected_client = _get_entry_and_client(hass, call)
        except HomeAssistantError as err:
            self.fail(f"Expected runtime data client, got error: {err}")

        self.assertIs(entry, selected_entry)
        self.assertIs(client, selected_client)

    async def test_unload_entry_deletes_missing_capability_repairs(self) -> None:
        hass = FakeHass()
        entry = FakeEntry()
        hass.data[DOMAIN] = {entry.entry_id: entry}

        self.assertTrue(await integration.async_unload_entry(hass, entry))

        self.assertEqual([(entry, PLATFORMS)], hass.config_entries.unloaded)
        self.assertNotIn(entry.entry_id, hass.data[DOMAIN])
        self.assertEqual(
            [
                (hass, DOMAIN, "missing_image_entry-1"),
                (hass, DOMAIN, "missing_tts_entry-1"),
                (hass, DOMAIN, "missing_stt_entry-1"),
            ],
            [call[0] for call in ir.DELETED],
        )

    async def test_setup_entry_stores_runtime_data_and_updates_capability_repairs(self) -> None:
        class Client:
            def __init__(
                self,
                session: Any,
                url: str,
                api_key: str | None = None,
                timeout: float = 30.0,
            ) -> None:
                self.session = session
                self.url = url
                self.api_key = api_key
                self.timeout = timeout

            async def health(self) -> dict[str, Any]:
                return {"status": "ok"}

            async def models(self) -> dict[str, Any]:
                return {
                    "data": [
                        {
                            "id": "image-model",
                            "recipe": "diffusers",
                            "labels": ["image"],
                        },
                        {"id": "voice-model", "recipe": "tts", "labels": ["tts"]},
                    ]
                }

        original_client = integration.LemonadeClient
        integration.LemonadeClient = Client
        self.addCleanup(setattr, integration, "LemonadeClient", original_client)
        hass = FakeHass()
        entry = FakeEntry()

        self.assertTrue(await integration.async_setup_entry(hass, entry))

        self.assertIsInstance(entry.runtime_data, LemonadeRuntimeData)
        self.assertIsInstance(entry.runtime_data.client, Client)
        self.assertEqual(
            ["image-model"],
            entry.runtime_data.coordinator.catalog.model_ids(CAPABILITY_IMAGE),
        )
        self.assertIs(hass.data[DOMAIN][entry.entry_id], entry)
        self.assertEqual([(entry, PLATFORMS)], hass.config_entries.forwarded)
        self.assertEqual(
            [
                (hass, DOMAIN, "missing_image_entry-1"),
                (hass, DOMAIN, "missing_tts_entry-1"),
            ],
            [call[0] for call in ir.DELETED],
        )
        self.assertEqual(
            [(hass, DOMAIN, "missing_stt_entry-1")],
            [call[0] for call in ir.CREATED],
        )


if __name__ == "__main__":
    unittest.main()
