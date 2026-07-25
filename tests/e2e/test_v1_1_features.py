"""End-to-end coverage for features added after v1.0.0."""

import asyncio
import json
from typing import Any
from urllib.parse import urlsplit

import pytest
from homeassistant import config_entries
from homeassistant.components import stt, tts
from homeassistant.components.ai_task import (
    ATTR_ENTITY_ID as AI_TASK_ENTITY_ID,
    ATTR_INSTRUCTIONS,
    ATTR_TASK_NAME,
    DOMAIN as AI_TASK_DOMAIN,
)
from homeassistant.components.ai_task.const import SERVICE_GENERATE_DATA
from homeassistant.components.conversation.const import (
    ATTR_AGENT_ID,
    ATTR_TEXT as CONVERSATION_TEXT,
    DOMAIN as CONVERSATION_DOMAIN,
    SERVICE_PROCESS,
)
from homeassistant.const import CONF_MODEL, CONF_NAME, CONF_PROMPT, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lemonade import beacon
from custom_components.lemonade.const import (
    ATTR_PROMPT,
    ATTR_ROUTE_TRACE,
    ATTR_ROUTER_METADATA,
    ATTR_TEXT,
    ATTR_TOP_K,
    CONF_MAX_HISTORY,
    CONF_ROUTER_METADATA,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    DEFAULT_MAX_HISTORY,
    DOMAIN,
    SERVICE_CHAT_COMPLETION,
    SERVICE_CLASSIFY_TEXT,
    STARTER_PROMPT,
    SUBENTRY_TYPE_AI_TASK,
    SUBENTRY_TYPE_CONVERSATION,
)


async def _create_profile(
    hass: HomeAssistant,
    entry: Any,
    profile_type: str,
    data: dict[str, Any],
) -> Any:
    """Create and load a profile through Home Assistant's subentry flow."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, profile_type),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        data,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return next(
        subentry
        for subentry in entry.subentries.values()
        if subentry.title == data[CONF_NAME]
    )


def _profile_entity_id(
    hass: HomeAssistant,
    entry: Any,
    subentry: Any,
    platform: str,
) -> str:
    """Resolve the entity Home Assistant registered for a profile."""
    registry = er.async_get(hass)
    matches = [
        registry_entry.entity_id
        for registry_entry in registry.entities.values()
        if registry_entry.config_entry_id == entry.entry_id
        and registry_entry.config_subentry_id == subentry.subentry_id
        and registry_entry.platform == DOMAIN
        and registry_entry.domain == platform
    ]
    assert len(matches) == 1
    return matches[0]


async def test_new_server_entry_provisions_starter_conversation_profile(
    hass: HomeAssistant,
    lemonade_server: tuple[str, list[dict[str, Any]]],
) -> None:
    """A confirmed Server Entry is immediately usable from Assist."""
    server_url, _ = lemonade_server
    assert await async_setup_component(hass, "homeassistant", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "End-to-end Lemonade",
            CONF_URL: server_url,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    entry = result["result"]
    assert entry.title == "End-to-end Lemonade"
    assert len(entry.subentries) == 1
    starter = next(iter(entry.subentries.values()))
    assert starter.title == "Lemonade Conversation"
    assert starter.subentry_type == SUBENTRY_TYPE_CONVERSATION
    assert dict(starter.data) == {
        CONF_NAME: "Lemonade Conversation",
        CONF_PROMPT: STARTER_PROMPT,
        CONF_MAX_HISTORY: DEFAULT_MAX_HISTORY,
    }


async def test_classification_service_preserves_server_scores(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """Automations receive the Classification Result without HA interpretation."""
    entry, _, requests = lemonade_entry

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_CLASSIFY_TEXT,
        {
            "entry_id": entry.entry_id,
            ATTR_TEXT: "Turn on the kitchen lights",
            ATTR_TOP_K: 2,
        },
        blocking=True,
        return_response=True,
    )

    assert response == {
        "model": "intent-classifier",
        "labels": {"automation": 0.91, "conversation": 0.09},
    }
    assert requests == [
        {
            "path": "/v1/classify",
            "payload": {
                "model": "intent-classifier",
                "text": "Turn on the kitchen lights",
                "top_k": 2,
            },
        }
    ]


async def test_direct_chat_returns_route_decision_and_passes_router_metadata(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """Direct chat exposes opt-in routing diagnostics without retaining them."""
    entry, _, requests = lemonade_entry

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_CHAT_COMPLETION,
        {
            "entry_id": entry.entry_id,
            "model": "house-router",
            ATTR_PROMPT: "Choose the best model for this request.",
            ATTR_ROUTE_TRACE: True,
            ATTR_ROUTER_METADATA: {
                "room": "kitchen",
                "priority": "local-first",
            },
        },
        blocking=True,
        return_response=True,
    )

    assert response["response"]["route_decision"] == {
        "selected_model": "local-chat",
        "reason": "local candidate",
    }
    assert response["content"] == "Lemonade end-to-end response"
    assert requests == [
        {
            "path": "/v1/chat/completions",
            "payload": {
                "model": "house-router",
                "messages": [
                    {
                        "role": "user",
                        "content": "Choose the best model for this request.",
                    }
                ],
                "stream": False,
                "route_trace": True,
                "metadata": {
                    "room": "kitchen",
                    "priority": "local-first",
                },
            },
        }
    ]


async def test_router_and_omni_profiles_run_through_assist_and_ai_task(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """Router and Omni models are selectable and executable as HA profiles."""
    entry, _, requests = lemonade_entry
    router_profile = await _create_profile(
        hass,
        entry,
        SUBENTRY_TYPE_CONVERSATION,
        {
            CONF_NAME: "House Router",
            CONF_MODEL: "house-router",
            CONF_PROMPT: "Route household requests.",
            CONF_MAX_HISTORY: 4,
            CONF_ROUTER_METADATA: {"surface": "assist", "home": "primary"},
        },
    )
    omni_profile = await _create_profile(
        hass,
        entry,
        SUBENTRY_TYPE_AI_TASK,
        {
            CONF_NAME: "House Omni",
            CONF_MODEL: "house-omni",
            CONF_PROMPT: "Return concise household data.",
            CONF_MAX_HISTORY: 2,
            CONF_ROUTER_METADATA: {"surface": "ai_task", "home": "primary"},
        },
    )

    conversation_entity = _profile_entity_id(
        hass,
        entry,
        router_profile,
        CONVERSATION_DOMAIN,
    )
    assist_response = await hass.services.async_call(
        CONVERSATION_DOMAIN,
        SERVICE_PROCESS,
        {
            CONVERSATION_TEXT: "What needs attention?",
            ATTR_AGENT_ID: conversation_entity,
        },
        blocking=True,
        return_response=True,
    )
    assert assist_response["response"]["speech"]["plain"]["speech"] == (
        "Lemonade end-to-end response"
    )

    ai_task_entity = _profile_entity_id(
        hass,
        entry,
        omni_profile,
        AI_TASK_DOMAIN,
    )
    task_response = await hass.services.async_call(
        AI_TASK_DOMAIN,
        SERVICE_GENERATE_DATA,
        {
            ATTR_TASK_NAME: "Summarize the home",
            AI_TASK_ENTITY_ID: ai_task_entity,
            ATTR_INSTRUCTIONS: "Summarize the rooms needing attention.",
        },
        blocking=True,
        return_response=True,
    )
    assert task_response["data"] == "Lemonade end-to-end response"

    chat_requests = [
        request["payload"]
        for request in requests
        if request["path"] == "/v1/chat/completions"
    ]
    assert [request["model"] for request in chat_requests] == [
        "house-router",
        "house-omni",
    ]
    assert chat_requests[0]["metadata"] == {
        "surface": "assist",
        "home": "primary",
    }
    assert chat_requests[1]["metadata"] == {
        "surface": "ai_task",
        "home": "primary",
    }


async def test_native_speech_entities_advertise_non_english_locales(
    hass: HomeAssistant,
    lemonade_entry: tuple[Any, str, list[dict[str, Any]]],
) -> None:
    """The native STT and TTS provider surfaces expose all HA locales."""
    del lemonade_entry
    assert {"de", "es", "fr"} <= stt.async_get_speech_to_text_languages(hass)
    assert {"de", "es", "fr"} <= tts.async_get_text_to_speech_languages(hass)


async def _send_beacon(endpoint: str, port: int) -> None:
    """Advertise one loopback server while the setup flow is listening."""
    parsed = urlsplit(endpoint)
    payload = json.dumps(
        {
            "service": "lemonade",
            "hostname": "e2e-lemonade",
            "url": f"http://127.0.0.1:{parsed.port}/api/v1/",
        }
    ).encode()
    await asyncio.sleep(0.1)
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        asyncio.DatagramProtocol,
        remote_addr=("127.0.0.1", port),
    )
    try:
        for _ in range(4):
            transport.sendto(payload)
            await asyncio.sleep(0.1)
    finally:
        transport.close()


async def test_udp_discovery_prefills_setup_and_endpoint_reconfiguration_succeeds(
    hass: HomeAssistant,
    lemonade_server: tuple[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
    unused_udp_port: int,
) -> None:
    """A beacon pre-fills setup and deliberate reconfiguration preserves profiles."""
    server_url, _ = lemonade_server
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "network", {})
    monkeypatch.setattr(beacon, "BEACON_PORT", unused_udp_port)

    sender = asyncio.create_task(_send_beacon(server_url, unused_udp_port))
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    await sender
    assert result["type"] is FlowResultType.FORM
    discovered = result["data_schema"]({})
    assert discovered[CONF_NAME] == "Lemonade Server — e2e-lemonade"
    assert discovered[CONF_URL] == server_url

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        discovered,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = result["result"]
    original_subentries = tuple(entry.subentries)

    reconfigure = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert reconfigure["type"] is FlowResultType.FORM
    replacement = f"{server_url}/replacement"
    reconfigure = await hass.config_entries.flow.async_configure(
        reconfigure["flow_id"],
        {CONF_URL: replacement},
    )
    assert reconfigure["type"] is FlowResultType.ABORT
    assert reconfigure["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert entry.data[CONF_URL] == replacement
    assert entry.unique_id == replacement
    assert tuple(entry.subentries) == original_subentries
    assert entry.state is config_entries.ConfigEntryState.LOADED


async def test_starter_profile_migrates_once_and_deleted_profile_stays_deleted(
    hass: HomeAssistant,
    lemonade_server: tuple[str, list[dict[str, Any]]],
) -> None:
    """A legacy entry is backfilled once; user deletion is then authoritative."""
    server_url, _ = lemonade_server
    assert await async_setup_component(hass, "homeassistant", {})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Legacy Lemonade",
        data={
            CONF_URL: server_url,
            CONF_TIMEOUT: 120.0,
            CONF_VERIFY_SSL: True,
        },
        unique_id=server_url,
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.minor_version == 2
    assert len(entry.subentries) == 1
    starter = next(iter(entry.subentries.values()))
    assert starter.subentry_type == SUBENTRY_TYPE_CONVERSATION

    assert hass.config_entries.async_remove_subentry(entry, starter.subentry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert entry.minor_version == 2
    assert entry.subentries == {}
