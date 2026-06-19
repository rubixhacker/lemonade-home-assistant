"""Tests for Lemonade runtime setup."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import Any
import unittest


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
    aiohttp_client.async_get_clientsession = lambda hass: "session"
    sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client)

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

from homeassistant.const import CONF_API_KEY, CONF_URL  # noqa: E402
from homeassistant.helpers import issue_registry as ir  # noqa: E402

import lemonade as integration  # noqa: E402
from lemonade.api import LemonadeClient  # noqa: E402
from lemonade.const import (  # noqa: E402
    CAPABILITY_IMAGE,
    CAPABILITY_STT,
    CAPABILITY_TTS,
    CONF_TIMEOUT,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    PLATFORMS,
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


class RuntimeSetupTest(unittest.IsolatedAsyncioTestCase):
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
