"""Tests for Lemonade runtime setup."""

from __future__ import annotations

import importlib
import inspect
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
    def _get_entry(self) -> Any:
        return self._flow_entry

    def _get_reconfigure_subentry(self) -> Any:
        return self._reconfigure_subentry_obj

    def async_update_and_abort(
        self, config_entry: Any, subentry: Any, *, data: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "type": "abort",
            "reason": "reconfigure_successful",
            "entry": config_entry,
            "subentry": subentry,
            "data": data,
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

    voluptuous_openapi = ModuleType("voluptuous_openapi")

    def convert(schema: Any, *, custom_serializer: Any = None) -> dict[str, Any]:
        return {"schema": schema, "custom_serializer": custom_serializer}

    voluptuous_openapi.convert = convert
    sys.modules.setdefault("voluptuous_openapi", voluptuous_openapi)

    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules.setdefault("homeassistant", homeassistant)

    components = ModuleType("homeassistant.components")
    components.__path__ = []
    sys.modules.setdefault("homeassistant.components", components)

    sensor_component = ModuleType("homeassistant.components.sensor")
    sensor_component.SensorEntity = type("SensorEntity", (), {})
    sensor_component.SensorStateClass = SimpleNamespace(MEASUREMENT="measurement")
    sys.modules.setdefault("homeassistant.components.sensor", sensor_component)
    components.sensor = sensor_component

    select_component = ModuleType("homeassistant.components.select")
    select_component.SelectEntity = type("SelectEntity", (), {})
    sys.modules.setdefault("homeassistant.components.select", select_component)
    components.select = select_component

    conversation_component = ModuleType("homeassistant.components.conversation")

    class SystemContent:
        def __init__(self, content: str) -> None:
            self.content = content

    class UserContent:
        def __init__(
            self, content: str, attachments: list[Any] | None = None
        ) -> None:
            self.content = content
            self.attachments = attachments or []

    class AssistantContent:
        def __init__(
            self, content: str | None = None, tool_calls: list[Any] | None = None
        ) -> None:
            self.content = content
            self.tool_calls = tool_calls or []

    class ToolResultContent:
        def __init__(
            self,
            tool_result: Any,
            tool_call_id: str | None = None,
            tool_name: str | None = None,
        ) -> None:
            self.tool_result = tool_result
            self.tool_call_id = tool_call_id
            self.tool_name = tool_name

    class ConversationEntity:
        pass

    class AbstractConversationAgent:
        pass

    class ConverseError(Exception):
        def as_conversation_result(self) -> dict[str, Any]:
            return {"error": str(self)}

    def async_set_agent(hass: Any, entry: Any, agent: Any) -> None:
        hass.set_agents.append((entry, agent))

    def async_unset_agent(hass: Any, entry: Any) -> None:
        hass.unset_agents.append(entry)

    def async_get_result_from_chat_log(user_input: Any, chat_log: Any) -> dict[str, Any]:
        return {
            "conversation_id": getattr(user_input, "conversation_id", None),
            "deltas": getattr(chat_log, "deltas", []),
        }

    conversation_component.SystemContent = SystemContent
    conversation_component.UserContent = UserContent
    conversation_component.AssistantContent = AssistantContent
    conversation_component.ToolResultContent = ToolResultContent
    conversation_component.AssistantContentDeltaDict = dict
    conversation_component.ChatLog = object
    conversation_component.ConversationInput = object
    conversation_component.ConversationResult = dict
    conversation_component.ConversationEntity = ConversationEntity
    conversation_component.AbstractConversationAgent = AbstractConversationAgent
    conversation_component.ConverseError = ConverseError
    conversation_component.ConversationEntityFeature = SimpleNamespace(CONTROL=1)
    conversation_component.MATCH_ALL = "*"
    conversation_component.async_set_agent = async_set_agent
    conversation_component.async_unset_agent = async_unset_agent
    conversation_component.async_get_result_from_chat_log = async_get_result_from_chat_log
    sys.modules.setdefault(
        "homeassistant.components.conversation", conversation_component
    )
    components.conversation = conversation_component

    ai_task_component = ModuleType("homeassistant.components.ai_task")

    class GenDataTaskResult:
        def __init__(self, *, conversation_id: str | None = None, data: Any = None) -> None:
            self.conversation_id = conversation_id
            self.data = data

    class GenImageTaskResult:
        def __init__(
            self,
            *,
            image_data: bytes,
            conversation_id: str | None = None,
            mime_type: str | None = None,
            model: str | None = None,
        ) -> None:
            self.image_data = image_data
            self.conversation_id = conversation_id
            self.mime_type = mime_type
            self.model = model

    ai_task_component.AITaskEntity = type("AITaskEntity", (), {})
    ai_task_component.AITaskEntityFeature = SimpleNamespace(
        GENERATE_DATA=1, GENERATE_IMAGE=2, SUPPORT_ATTACHMENTS=4
    )
    ai_task_component.GenDataTaskResult = GenDataTaskResult
    ai_task_component.GenImageTaskResult = GenImageTaskResult
    sys.modules.setdefault("homeassistant.components.ai_task", ai_task_component)
    components.ai_task = ai_task_component

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

    util = ModuleType("homeassistant.util")
    util.__path__ = []
    util_json = ModuleType("homeassistant.util.json")
    util_json.json_dumps = lambda value: json.dumps(value, sort_keys=True)
    sys.modules.setdefault("homeassistant.util", util)
    sys.modules.setdefault("homeassistant.util.json", util_json)

    config_validation = ModuleType("homeassistant.helpers.config_validation")
    config_validation.config_entry_only_config_schema = lambda domain: None
    config_validation.string = str
    sys.modules.setdefault(
        "homeassistant.helpers.config_validation",
        config_validation,
    )
    helpers.config_validation = config_validation


    device_registry = ModuleType("homeassistant.helpers.device_registry")

    class DeviceInfo(dict):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)

    device_registry.DeviceEntryType = SimpleNamespace(SERVICE="service")
    device_registry.DeviceInfo = DeviceInfo
    sys.modules.setdefault("homeassistant.helpers.device_registry", device_registry)
    helpers.device_registry = device_registry

    entity_platform = ModuleType("homeassistant.helpers.entity_platform")
    entity_platform.AddEntitiesCallback = object
    sys.modules.setdefault("homeassistant.helpers.entity_platform", entity_platform)
    helpers.entity_platform = entity_platform

    aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = lambda hass: "session"
    sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client)

    llm = ModuleType("homeassistant.helpers.llm")

    class ToolInput:
        def __init__(
            self,
            *,
            tool_name: str,
            tool_args: dict[str, Any] | None = None,
            id: str | None = None,
        ) -> None:
            self.tool_name = tool_name
            self.tool_args = tool_args or {}
            self.id = id

        def __eq__(self, other: Any) -> bool:
            return (
                isinstance(other, ToolInput)
                and self.tool_name == other.tool_name
                and self.tool_args == other.tool_args
                and self.id == other.id
            )

    llm.ToolInput = ToolInput
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


    class CoordinatorEntity:
        def __init__(self, coordinator: Any) -> None:
            self.coordinator = coordinator
            self.hass = getattr(coordinator, "hass", None)

        @classmethod
        def __class_getitem__(cls, item: Any) -> type["CoordinatorEntity"]:
            return cls

        @property
        def available(self) -> bool:
            return getattr(self.coordinator, "last_update_success", True)

    update_coordinator.CoordinatorEntity = CoordinatorEntity
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    sys.modules.setdefault("homeassistant.helpers.update_coordinator", update_coordinator)

    typing = ModuleType("homeassistant.helpers.typing")
    typing.ConfigType = dict
    sys.modules.setdefault("homeassistant.helpers.typing", typing)


_install_homeassistant_stubs()


def _require_module(module_name: str) -> ModuleType:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise AssertionError(f"{module_name} should exist")
    return importlib.import_module(module_name)

from homeassistant.components.sensor import SensorStateClass  # noqa: E402
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
        self.updated: list[tuple[Any, dict[str, Any]]] = []

    async def async_forward_entry_setups(self, entry: Any, platforms: Any) -> None:
        self.forwarded.append((entry, platforms))

    async def async_unload_platforms(self, entry: Any, platforms: Any) -> bool:
        self.unloaded.append((entry, platforms))
        return True

    def async_update_entry(self, entry: Any, **kwargs: Any) -> None:
        self.updated.append((entry, kwargs))
        if "options" in kwargs:
            entry.options = kwargs["options"]

    async def async_reload(self, entry_id: str) -> None:
        self.reloaded = entry_id


class FakeHass:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.config_entries = FakeConfigEntries()
        self.set_agents: list[tuple[Any, Any]] = []
        self.unset_agents: list[Any] = []


class FakeEntry:
    entry_id = "entry-1"
    title = "Lemonade Server"
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


def _profile_flow(entry: Any, subentry_type: str, subentry: Any | None = None) -> Any:
    from lemonade.config_flow import LemonadeProfileSubentryFlow

    flow = LemonadeProfileSubentryFlow()
    flow._flow_entry = entry
    flow._reconfigure_subentry_obj = subentry
    flow.context = {"subentry_type": subentry_type}
    return flow


class FakeCatalog:
    def __init__(self, model_ids: dict[str, list[str]]) -> None:
        self._model_ids = model_ids
        all_model_ids = dict.fromkeys(
            model_id for ids in model_ids.values() for model_id in ids
        )
        self.models = tuple(SimpleNamespace(id=model_id) for model_id in all_model_ids)

    def model_ids(self, capability: str) -> list[str]:
        return list(self._model_ids.get(capability, []))

    def models_for(self, capability: str) -> tuple[Any, ...]:
        return tuple(
            SimpleNamespace(id=model_id) for model_id in self._model_ids.get(capability, [])
        )


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

    def test_profile_subentry_flow_uses_home_assistant_no_arg_constructor(self) -> None:
        from lemonade.config_flow import LemonadeProfileSubentryFlow

        self.assertEqual(
            [],
            list(inspect.signature(LemonadeProfileSubentryFlow).parameters),
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
        flow = _profile_flow(entry, SUBENTRY_TYPE_AI_TASK)
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
        flow = _profile_flow(entry, SUBENTRY_TYPE_CONVERSATION)
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
        flow = _profile_flow(entry, SUBENTRY_TYPE_CONVERSATION, subentry)
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
        self.assertIs(entry, result["entry"])
        self.assertIs(subentry, result["subentry"])
        self.assertEqual(submitted, result["data"])
        self.assertNotIn("title", result)

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

    async def test_options_flow_omits_blank_api_key_submission(self) -> None:
        from lemonade.config_flow import LemonadeOptionsFlow

        entry = SimpleNamespace(
            data={CONF_API_KEY: "secret", CONF_TIMEOUT: 12.0},
            options={},
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(catalog=FakeCatalog({}))
            ),
        )
        submitted = {CONF_API_KEY: "   ", CONF_TIMEOUT: 9.5}

        result = await LemonadeOptionsFlow(entry).async_step_init(submitted)

        self.assertEqual(9.5, result["data"][CONF_TIMEOUT])
        self.assertNotIn(CONF_API_KEY, result["data"])

    async def test_options_flow_preserves_existing_option_api_key_when_blank(
        self,
    ) -> None:
        from lemonade.config_flow import LemonadeOptionsFlow

        entry = SimpleNamespace(
            data={CONF_API_KEY: "secret", CONF_TIMEOUT: 12.0},
            options={CONF_API_KEY: "override"},
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(catalog=FakeCatalog({}))
            ),
        )
        submitted = {CONF_API_KEY: "", CONF_TIMEOUT: 9.5}

        result = await LemonadeOptionsFlow(entry).async_step_init(submitted)

        self.assertEqual("override", result["data"][CONF_API_KEY])
        self.assertEqual(9.5, result["data"][CONF_TIMEOUT])

    def setUp(self) -> None:
        ir.CREATED.clear()
        ir.DELETED.clear()

    async def test_api_models_returns_raw_list_response(self) -> None:
        client = LemonadeClient(FakeSession([{"id": "raw-model"}]), "http://server")

        models = await client.models()

        self.assertEqual([{"id": "raw-model"}], models)

    async def test_chat_completion_accepts_tools_and_response_format(self) -> None:
        session = FakeSession({"choices": []})
        client = LemonadeClient(session, "http://server")
        tools = [{"type": "function", "function": {"name": "turn_on"}}]
        response_format = {"type": "json_object"}

        try:
            await client.chat_completion(
                model="chat-model",
                messages=[{"role": "user", "content": "Hi"}],
                tools=tools,
                response_format=response_format,
            )
        except TypeError as err:
            self.fail(f"chat_completion should accept tools and response_format: {err}")

        payload = session.requests[-1][2]["json"]
        self.assertEqual(tools, payload["tools"])
        self.assertEqual(response_format, payload["response_format"])

        await client.chat_completion(
            model="chat-model", messages=[{"role": "user", "content": "Hi"}]
        )

        payload = session.requests[-1][2]["json"]
        self.assertNotIn("tools", payload)
        self.assertNotIn("response_format", payload)

    def test_llm_converts_content_and_tools_to_openai_shapes(self) -> None:
        from homeassistant.components.conversation import (
            AssistantContent,
            ToolResultContent,
            UserContent,
        )
        from homeassistant.exceptions import HomeAssistantError

        llm_module = _require_module("lemonade.llm")
        tool = SimpleNamespace(
            name="HassTurnOn",
            description="Turn on an entity",
            parameters={"type": "object"},
        )

        formatted_tool = llm_module.format_tool(tool, "serializer")

        self.assertEqual(
            {
                "type": "function",
                "function": {
                    "name": "HassTurnOn",
                    "description": "Turn on an entity",
                    "parameters": {
                        "schema": {"type": "object"},
                        "custom_serializer": "serializer",
                    },
                },
            },
            formatted_tool,
        )

        image_message = llm_module.content_to_message(
            UserContent(
                "Look",
                attachments=[
                    SimpleNamespace(mime_type="image/png", content=b"image-bytes")
                ],
            )
        )
        self.assertEqual("user", image_message["role"])
        self.assertEqual({"type": "text", "text": "Look"}, image_message["content"][0])
        self.assertEqual(
            "data:image/png;base64,aW1hZ2UtYnl0ZXM=",
            image_message["content"][1]["image_url"]["url"],
        )

        assistant_message = llm_module.content_to_message(
            AssistantContent(
                "I will help",
                tool_calls=[
                    SimpleNamespace(
                        id="call-1",
                        tool_name="HassTurnOn",
                        tool_args={"entity_id": "light.kitchen"},
                    )
                ],
            )
        )
        self.assertEqual("assistant", assistant_message["role"])
        self.assertEqual("I will help", assistant_message["content"])
        self.assertEqual(
            [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "HassTurnOn",
                        "arguments": '{"entity_id": "light.kitchen"}',
                    },
                }
            ],
            assistant_message["tool_calls"],
        )

        tool_result_message = llm_module.content_to_message(
            ToolResultContent(
                {"ok": True}, tool_call_id="call-1", tool_name="HassTurnOn"
            )
        )
        self.assertEqual(
            {
                "role": "tool",
                "content": '{"ok": true}',
                "tool_call_id": "call-1",
                "name": "HassTurnOn",
            },
            tool_result_message,
        )

        with self.assertRaises(HomeAssistantError):
            llm_module.content_to_message(
                UserContent(
                    "Read",
                    attachments=[
                        SimpleNamespace(mime_type="application/pdf", content=b"pdf")
                    ],
                )
            )

    def test_llm_converts_tool_result_object_payloads(self) -> None:
        from homeassistant.components.conversation import ToolResultContent

        llm_module = _require_module("lemonade.llm")

        message = llm_module.content_to_message(
            ToolResultContent(
                SimpleNamespace(
                    tool_name="HassTurnOn",
                    result={"ok": True},
                ),
                tool_call_id="call-1",
                tool_name="HassTurnOn",
            )
        )

        self.assertEqual(
            {
                "role": "tool",
                "content": '{"ok": true}',
                "tool_call_id": "call-1",
                "name": "HassTurnOn",
            },
            message,
        )

    def test_llm_assistant_content_without_text_or_tool_calls_uses_empty_string(self) -> None:
        from homeassistant.components.conversation import AssistantContent

        llm_module = _require_module("lemonade.llm")

        message = llm_module.content_to_message(AssistantContent(None))

        self.assertEqual({"role": "assistant", "content": ""}, message)

    def test_llm_preserves_tool_result_mapping_payload_without_using_payload_metadata(self) -> None:
        from homeassistant.components.conversation import ToolResultContent

        llm_module = _require_module("lemonade.llm")
        payload = {
            "result": "ok",
            "other": 1,
            "tool_call_id": "payload-call",
            "tool_name": "PayloadTool",
        }

        message = llm_module.content_to_message(ToolResultContent(payload))

        self.assertEqual("tool", message["role"])
        self.assertEqual(payload, json.loads(message["content"]))
        self.assertNotIn("tool_call_id", message)
        self.assertNotIn("name", message)

    def test_llm_response_to_delta_returns_single_chat_log_delta(self) -> None:
        from homeassistant.helpers.llm import ToolInput

        llm_module = _require_module("lemonade.llm")

        delta = llm_module.response_to_delta(
            {
                "choices": [
                    {
                        "message": {
                            "content": "Done",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "HassTurnOn",
                                        "arguments": '{"entity_id": "light.kitchen"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )

        self.assertEqual(
            {
                "content": "Done",
                "tool_calls": [
                    ToolInput(
                        id="call-1",
                        tool_name="HassTurnOn",
                        tool_args={"entity_id": "light.kitchen"},
                    )
                ],
            },
            delta,
        )

    async def test_llm_handle_chat_log_adds_response_delta_and_passes_tools(self) -> None:
        from homeassistant.components.conversation import SystemContent, UserContent
        from homeassistant.helpers.llm import ToolInput

        llm_module = _require_module("lemonade.llm")

        class Client:
            def __init__(self) -> None:
                self.calls: list[dict[str, Any]] = []

            async def chat_completion(self, **kwargs: Any) -> dict[str, Any]:
                self.calls.append(kwargs)
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "Done",
                                "tool_calls": [
                                    {
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {
                                            "name": "HassTurnOn",
                                            "arguments": '{"entity_id": "light.kitchen"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }

        class ChatLog:
            def __init__(self) -> None:
                self.content = [SystemContent("You are helpful"), UserContent("Hi")]
                self.llm_api = SimpleNamespace(
                    tools=[
                        SimpleNamespace(
                            name="HassTurnOn",
                            description=None,
                            parameters={"type": "object"},
                        )
                    ],
                    custom_serializer="serializer",
                )
                self.unresponded_tool_results: list[Any] = []
                self.deltas: list[dict[str, Any]] = []
                self.agent_ids: list[str] = []

            async def async_add_delta_content_stream(
                self, agent_id: str, stream: Any
            ) -> None:
                self.agent_ids.append(agent_id)
                async for delta in stream:
                    self.deltas.append(delta)

        client = Client()
        chat_log = ChatLog()

        await llm_module.async_handle_chat_log(
            "conversation.lemonade",
            client,
            "chat-model",
            chat_log,
            structure={"type": "json_object"},
        )

        self.assertEqual(["conversation.lemonade"], chat_log.agent_ids)
        self.assertEqual("chat-model", client.calls[0]["model"])
        self.assertEqual(
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hi"},
            ],
            client.calls[0]["messages"],
        )
        self.assertEqual(
            [
                {
                    "type": "function",
                    "function": {
                        "name": "HassTurnOn",
                        "parameters": {
                            "schema": {"type": "object"},
                            "custom_serializer": "serializer",
                        },
                    },
                }
            ],
            client.calls[0]["tools"],
        )
        self.assertEqual({"type": "json_object"}, client.calls[0]["response_format"])
        self.assertEqual(
            [
                {
                    "content": "Done",
                    "tool_calls": [
                        ToolInput(
                            id="call-1",
                            tool_name="HassTurnOn",
                            tool_args={"entity_id": "light.kitchen"},
                        )
                    ],
                }
            ],
            chat_log.deltas,
        )

    async def test_conversation_platform_adds_only_conversation_subentries(self) -> None:
        conversation_module = _require_module("lemonade.conversation")
        entry = SimpleNamespace(
            subentries={
                "conv-1": SimpleNamespace(
                    subentry_id="conv-1",
                    subentry_type=SUBENTRY_TYPE_CONVERSATION,
                    data={},
                ),
                "task-1": SimpleNamespace(
                    subentry_id="task-1",
                    subentry_type=SUBENTRY_TYPE_AI_TASK,
                    data={},
                ),
            }
        )
        calls: list[tuple[list[Any], dict[str, Any]]] = []

        def add_entities(entities: list[Any], **kwargs: Any) -> None:
            calls.append((entities, kwargs))

        await conversation_module.async_setup_entry(FakeHass(), entry, add_entities)

        self.assertEqual(1, len(calls))
        self.assertEqual({"config_subentry_id": "conv-1"}, calls[0][1])
        entity = calls[0][0][0]
        self.assertIsInstance(entity, conversation_module.LemonadeConversationEntity)
        self.assertEqual("conv-1", entity._attr_unique_id)
        self.assertIsNone(entity._attr_name)
        self.assertTrue(entity._attr_has_entity_name)
        self.assertFalse(entity._attr_supports_streaming)

    async def test_ai_task_platform_adds_only_ai_task_subentries_and_features(self) -> None:
        from homeassistant.components import ai_task

        ai_task_module = _require_module("lemonade.ai_task")
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Lemonade Server",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_IMAGE: ["image-a"]})
                )
            ),
            subentries={
                "conv-1": SimpleNamespace(
                    subentry_id="conv-1",
                    subentry_type=SUBENTRY_TYPE_CONVERSATION,
                    data={},
                ),
                "task-1": SimpleNamespace(
                    subentry_id="task-1",
                    subentry_type=SUBENTRY_TYPE_AI_TASK,
                    data={},
                ),
            },
        )
        calls: list[tuple[list[Any], dict[str, Any]]] = []

        def add_entities(entities: list[Any], **kwargs: Any) -> None:
            calls.append((entities, kwargs))

        await ai_task_module.async_setup_entry(FakeHass(), entry, add_entities)

        self.assertEqual(1, len(calls))
        self.assertEqual({"config_subentry_id": "task-1"}, calls[0][1])
        entity = calls[0][0][0]
        self.assertIsInstance(entity, ai_task_module.LemonadeAITaskEntity)
        self.assertEqual("task-1", entity._attr_unique_id)
        self.assertIsNone(entity._attr_name)
        self.assertTrue(entity._attr_has_entity_name)
        self.assertEqual(
            ai_task.AITaskEntityFeature.GENERATE_DATA
            | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
            | ai_task.AITaskEntityFeature.GENERATE_IMAGE,
            entity._attr_supported_features,
        )

    async def test_ai_task_generate_data_prefers_profile_model_and_parses_structured_json(self) -> None:
        from homeassistant.components import ai_task
        from homeassistant.components.conversation import UserContent

        ai_task_module = _require_module("lemonade.ai_task")

        class Client:
            def __init__(self) -> None:
                self.calls: list[dict[str, Any]] = []

            async def chat_completion(self, **kwargs: Any) -> dict[str, Any]:
                self.calls.append(kwargs)
                return {"choices": [{"message": {"content": '{"ok": true}'}}]}

        class ChatLog:
            conversation_id = "conversation-1"

            def __init__(self) -> None:
                self.content = [UserContent("Return JSON")]
                self.llm_api = None
                self.unresponded_tool_results: list[Any] = []
                self.deltas: list[dict[str, Any]] = []

            async def async_add_delta_content_stream(
                self, agent_id: str, stream: Any
            ) -> None:
                async for delta in stream:
                    self.deltas.append(delta)

        client = Client()
        entry = SimpleNamespace(
            options={CONF_DEFAULT_AI_TASK_MODEL: "entry-task"},
            runtime_data=SimpleNamespace(
                client=client,
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_AI_TASK: ["catalog-task"]})
                ),
            ),
        )
        subentry = SimpleNamespace(
            subentry_id="task-1",
            data={CONF_MODEL: "profile-task"},
        )
        entity = ai_task_module.LemonadeAITaskEntity(entry, subentry)
        entity.entity_id = "ai_task.lemonade"

        result = await entity._async_generate_data(
            SimpleNamespace(structure={"type": "json_object"}),
            ChatLog(),
        )

        self.assertIsInstance(result, ai_task.GenDataTaskResult)
        self.assertEqual("conversation-1", result.conversation_id)
        self.assertEqual({"ok": True}, result.data)
        self.assertEqual("profile-task", client.calls[0]["model"])
        self.assertEqual(
            {"type": "json_object"}, client.calls[0]["response_format"]
        )

    async def test_ai_task_generate_image_decodes_response_and_uses_default_image_model(self) -> None:
        from homeassistant.components import ai_task

        ai_task_module = _require_module("lemonade.ai_task")

        class Client:
            def __init__(self) -> None:
                self.calls: list[dict[str, Any]] = []

            async def generate_image(self, **kwargs: Any) -> dict[str, Any]:
                self.calls.append(kwargs)
                return {"data": [{"b64_json": "aW1hZ2UtYnl0ZXM="}]}

        client = Client()
        entry = SimpleNamespace(
            options={CONF_DEFAULT_IMAGE_MODEL: "entry-image"},
            runtime_data=SimpleNamespace(
                client=client,
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_IMAGE: ["catalog-image"]})
                ),
            ),
        )
        entity = ai_task_module.LemonadeAITaskEntity(
            entry, SimpleNamespace(subentry_id="task-1", data={})
        )

        result = await entity._async_generate_image(
            SimpleNamespace(instructions="Draw a lemon"),
            SimpleNamespace(conversation_id="conversation-1"),
        )

        self.assertIsInstance(result, ai_task.GenImageTaskResult)
        self.assertEqual(b"image-bytes", result.image_data)
        self.assertEqual("conversation-1", result.conversation_id)
        self.assertEqual("image/png", result.mime_type)
        self.assertEqual("entry-image", result.model)
        self.assertEqual(
            [{"prompt": "Draw a lemon", "model": "entry-image"}],
            client.calls,
        )

    async def test_ai_task_generate_image_decodes_object_data_url_and_uses_catalog_model(self) -> None:
        from homeassistant.components import ai_task

        ai_task_module = _require_module("lemonade.ai_task")

        class Client:
            async def generate_image(self, **kwargs: Any) -> Any:
                return SimpleNamespace(
                    data=[
                        SimpleNamespace(
                            image="data:image/png;base64,aW1hZ2UtYnl0ZXM="
                        )
                    ]
                )

        entry = SimpleNamespace(
            options={},
            runtime_data=SimpleNamespace(
                client=Client(),
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_IMAGE: ["catalog-image"]})
                ),
            ),
        )
        entity = ai_task_module.LemonadeAITaskEntity(
            entry, SimpleNamespace(subentry_id="task-1", data={})
        )

        result = await entity._async_generate_image(
            SimpleNamespace(instructions="Draw a lemon"),
            SimpleNamespace(conversation_id="conversation-1"),
        )

        self.assertIsInstance(result, ai_task.GenImageTaskResult)
        self.assertEqual(b"image-bytes", result.image_data)
        self.assertEqual("catalog-image", result.model)

    async def test_conversation_entity_handles_message_with_resolved_model(self) -> None:
        from homeassistant.components import conversation

        conversation_module = _require_module("lemonade.conversation")

        class Client:
            def __init__(self) -> None:
                self.models: list[str] = []

            async def chat_completion(self, **kwargs: Any) -> dict[str, Any]:
                self.models.append(kwargs["model"])
                return {"choices": [{"message": {"content": "Hello"}}]}

        class ChatLog:
            def __init__(self) -> None:
                self.content = []
                self.llm_api = None
                self.unresponded_tool_results: list[Any] = []
                self.provided: list[tuple[Any, Any, Any, Any]] = []
                self.deltas: list[dict[str, Any]] = []

            async def async_provide_llm_data(self, *args: Any) -> None:
                self.provided.append(args)

            async def async_add_delta_content_stream(
                self, agent_id: str, stream: Any
            ) -> None:
                async for delta in stream:
                    self.deltas.append(delta)

        client = Client()
        entry = SimpleNamespace(
            options={CONF_DEFAULT_CONVERSATION_MODEL: "entry-chat"},
            runtime_data=SimpleNamespace(
                client=client,
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_CONVERSATION: ["catalog-chat"]})
                ),
            ),
        )
        subentry = SimpleNamespace(
            subentry_id="conv-1",
            data={
                CONF_LLM_HASS_API: ["assist"],
                CONF_PROMPT: "Be helpful",
            },
        )
        entity = conversation_module.LemonadeConversationEntity(entry, subentry)
        entity.hass = FakeHass()
        entity.entity_id = "conversation.lemonade"
        chat_log = ChatLog()
        user_input = SimpleNamespace(
            conversation_id="abc",
            extra_system_prompt="extra",
            as_llm_context=lambda domain: {"domain": domain},
        )

        self.assertEqual(
            conversation.ConversationEntityFeature.CONTROL,
            entity._attr_supported_features,
        )
        self.assertEqual(conversation.MATCH_ALL, entity.supported_languages)

        await entity.async_added_to_hass()
        await entity.async_will_remove_from_hass()
        result = await entity._async_handle_message(user_input, chat_log)

        self.assertEqual([(entry, entity)], entity.hass.set_agents)
        self.assertEqual([entry], entity.hass.unset_agents)
        self.assertEqual(["entry-chat"], client.models)
        self.assertEqual(
            [({"domain": DOMAIN}, ["assist"], "Be helpful", "extra")],
            chat_log.provided,
        )
        self.assertEqual(
            {"conversation_id": "abc", "deltas": [{"content": "Hello"}]},
            result,
        )

        subentry.data[CONF_MODEL] = "profile-chat"
        await entity._async_handle_message(user_input, ChatLog())
        self.assertEqual("profile-chat", client.models[-1])

    async def test_conversation_entity_errors_when_no_model_is_available(self) -> None:
        from homeassistant.exceptions import HomeAssistantError

        conversation_module = _require_module("lemonade.conversation")
        entry = SimpleNamespace(
            options={},
            runtime_data=SimpleNamespace(
                client=object(),
                coordinator=SimpleNamespace(catalog=FakeCatalog({CAPABILITY_CONVERSATION: []})),
            ),
        )
        entity = conversation_module.LemonadeConversationEntity(
            entry, SimpleNamespace(subentry_id="conv-1", data={})
        )

        with self.assertRaisesRegex(
            HomeAssistantError, "No Lemonade conversation model is available"
        ):
            await entity._async_handle_message(SimpleNamespace(), SimpleNamespace())

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
        flow = _profile_flow(entry, SUBENTRY_TYPE_CONVERSATION)

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
        flow = _profile_flow(entry, SUBENTRY_TYPE_CONVERSATION)

        result = await flow.async_step_user()

        self.assertEqual({"type": "abort", "reason": "no_models"}, result)

    async def test_profile_subentry_flow_aborts_unknown_profile_type(self) -> None:
        entry = SimpleNamespace(
            state="loaded",
            runtime_data=SimpleNamespace(
                coordinator=SimpleNamespace(
                    catalog=FakeCatalog({CAPABILITY_CONVERSATION: ["chat-a"]})
                )
            ),
        )
        flow = _profile_flow(entry, "unsupported")

        result = await flow.async_step_user()

        self.assertEqual(
            {"type": "abort", "reason": "unknown_profile_type"},
            result,
        )

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
        self.assertEqual(
            "Unsupported Lemonade profile type.",
            strings["config"]["abort"]["unknown_profile_type"],
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


    def test_entity_base_sets_unique_id_and_service_device_info(self) -> None:
        entity_module = _require_module("lemonade.entity")
        hass = FakeHass()
        coordinator = SimpleNamespace(
            hass=hass,
            catalog=FakeCatalog({}),
            last_update_success=True,
        )
        entry = FakeEntry()
        entry.title = "Kitchen Lemonade"
        entry.runtime_data = SimpleNamespace(coordinator=coordinator)

        entity = entity_module.LemonadeEntity(entry, "server_status")

        self.assertIs(entity.coordinator, coordinator)
        self.assertIs(entity.entry, entry)
        self.assertTrue(entity._attr_has_entity_name)
        self.assertEqual("entry-1_server_status", entity._attr_unique_id)
        self.assertEqual(
            {
                "identifiers": {(DOMAIN, entry.entry_id)},
                "name": "Kitchen Lemonade",
                "manufacturer": "Lemonade Server",
                "entry_type": "service",
            },
            dict(entity._attr_device_info),
        )

    async def test_sensor_platform_adds_status_and_model_count_entities(self) -> None:
        sensor_module = _require_module("lemonade.sensor")
        hass = FakeHass()
        coordinator = SimpleNamespace(
            hass=hass,
            last_update_success=True,
            catalog=FakeCatalog(
                {
                    CAPABILITY_CONVERSATION: ["chat-a", "chat-b"],
                    CAPABILITY_IMAGE: ["image-a"],
                    CAPABILITY_TTS: ["voice-a"],
                    CAPABILITY_STT: [],
                }
            ),
        )
        entry = FakeEntry()
        entry.runtime_data = SimpleNamespace(coordinator=coordinator)
        added: list[Any] = []

        await sensor_module.async_setup_entry(hass, entry, added.extend)

        entities = {entity._attr_translation_key: entity for entity in added}
        self.assertEqual(
            {
                "server_status",
                "model_count",
                "conversation_model_count",
                "image_model_count",
                "tts_model_count",
                "stt_model_count",
            },
            set(entities),
        )
        self.assertEqual("online", entities["server_status"].native_value)
        coordinator.last_update_success = False
        self.assertEqual("offline", entities["server_status"].native_value)
        self.assertTrue(entities["server_status"].available)
        self.assertIsNone(
            getattr(entities["server_status"], "_attr_state_class", None)
        )
        self.assertEqual(4, entities["model_count"].native_value)
        self.assertEqual(
            SensorStateClass.MEASUREMENT,
            getattr(entities["model_count"], "_attr_state_class", None),
        )
        self.assertEqual(2, entities["conversation_model_count"].native_value)
        self.assertEqual(
            SensorStateClass.MEASUREMENT,
            getattr(entities["conversation_model_count"], "_attr_state_class", None),
        )
        self.assertEqual(1, entities["image_model_count"].native_value)
        self.assertEqual(
            SensorStateClass.MEASUREMENT,
            getattr(entities["image_model_count"], "_attr_state_class", None),
        )
        self.assertEqual(1, entities["tts_model_count"].native_value)
        self.assertEqual(
            SensorStateClass.MEASUREMENT,
            getattr(entities["tts_model_count"], "_attr_state_class", None),
        )
        self.assertEqual(0, entities["stt_model_count"].native_value)
        self.assertEqual(
            SensorStateClass.MEASUREMENT,
            getattr(entities["stt_model_count"], "_attr_state_class", None),
        )

    async def test_select_platform_adds_default_model_selects_and_updates_options(self) -> None:
        select_module = _require_module("lemonade.select")
        hass = FakeHass()
        coordinator = SimpleNamespace(
            hass=hass,
            last_update_success=True,
            catalog=FakeCatalog(
                {
                    CAPABILITY_CONVERSATION: ["chat-a", "chat-b"],
                    CAPABILITY_AI_TASK: ["task-a"],
                    CAPABILITY_IMAGE: ["image-a"],
                    CAPABILITY_TTS: [],
                    CAPABILITY_STT: ["stt-a"],
                }
            ),
        )
        entry = FakeEntry()
        entry.options = {CONF_DEFAULT_CONVERSATION_MODEL: "chat-b"}
        entry.runtime_data = SimpleNamespace(coordinator=coordinator)
        added: list[Any] = []

        await select_module.async_setup_entry(hass, entry, added.extend)

        entities = {entity._attr_translation_key: entity for entity in added}
        self.assertEqual(
            {
                CONF_DEFAULT_CONVERSATION_MODEL,
                CONF_DEFAULT_AI_TASK_MODEL,
                CONF_DEFAULT_IMAGE_MODEL,
                CONF_DEFAULT_TTS_MODEL,
                CONF_DEFAULT_STT_MODEL,
            },
            set(entities),
        )
        self.assertEqual(
            ["chat-a", "chat-b"],
            entities[CONF_DEFAULT_CONVERSATION_MODEL].options,
        )
        self.assertEqual(
            "chat-b", entities[CONF_DEFAULT_CONVERSATION_MODEL].current_option
        )
        self.assertEqual("task-a", entities[CONF_DEFAULT_AI_TASK_MODEL].current_option)
        self.assertEqual([], entities[CONF_DEFAULT_TTS_MODEL].options)
        self.assertFalse(entities[CONF_DEFAULT_TTS_MODEL].available)
        self.assertIsNone(entities[CONF_DEFAULT_TTS_MODEL].current_option)

        await entities[CONF_DEFAULT_AI_TASK_MODEL].async_select_option("task-a")

        self.assertEqual(
            [
                (
                    entry,
                    {
                        "options": {
                            CONF_DEFAULT_CONVERSATION_MODEL: "chat-b",
                            CONF_DEFAULT_AI_TASK_MODEL: "task-a",
                        }
                    },
                )
            ],
            hass.config_entries.updated,
        )
        self.assertEqual("entry-1", hass.config_entries.reloaded)

    def test_strings_define_status_sensor_and_default_model_select_translations(self) -> None:
        strings = json.loads(Path("lemonade/strings.json").read_text())

        sensor_strings = strings.get("entity", {}).get("sensor", {})
        self.assertEqual(
            {
                "server_status",
                "model_count",
                "conversation_model_count",
                "image_model_count",
                "tts_model_count",
                "stt_model_count",
            },
            set(sensor_strings),
        )
        select_strings = strings.get("entity", {}).get("select", {})
        self.assertEqual(
            {
                CONF_DEFAULT_CONVERSATION_MODEL,
                CONF_DEFAULT_AI_TASK_MODEL,
                CONF_DEFAULT_IMAGE_MODEL,
                CONF_DEFAULT_TTS_MODEL,
                CONF_DEFAULT_STT_MODEL,
            },
            set(select_strings),
        )


if __name__ == "__main__":
    unittest.main()
