"""Exercise the real HA runtime against a real Lemonade container, without mocks."""

import asyncio
import datetime
import json
import logging
import os

import aiohttp
from homeassistant import bootstrap, loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

URL = "http://lemonade:13305/api"
MODEL = os.environ["E2E_MODEL"]


async def prepare_server():
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with asyncio.timeout(180):
            while True:
                try:
                    async with session.get(f"{URL}/v1/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        print("Lemonade health:", await response.json())
                    break
                except (aiohttp.ClientError, TimeoutError):
                    await asyncio.sleep(2)
        async with session.post(
            f"{URL}/v1/pull", json={"model_name": MODEL},
            timeout=aiohttp.ClientTimeout(total=900),
        ) as response:
            # Some server versions stream download progress. Consume it completely.
            body = await response.text()
            print("Model pull:", body[-2000:])


async def exercise(hass):
    loader.async_setup(hass)
    assert await bootstrap.async_from_config_dict(
        {"homeassistant": {"name": "Lemonade E2E", "time_zone": "UTC"}}, hass
    ) is not None, "HA bootstrap failed"
    await hass.async_start()
    result = await hass.config_entries.flow.async_init(
        "lemonade", context={"source": "user"},
        data={"name": "E2E", "url": URL, "timeout": 300.0, "verify_ssl": True},
    )
    assert result["type"] == "create_entry", result
    entry = result["result"]
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED, entry.state

    def check_sensors():
        registry = er.async_get(hass)
        sensors = {
            item.unique_id: hass.states.get(item.entity_id)
            for item in er.async_entries_for_config_entry(registry, entry.entry_id)
            if item.domain == "sensor"
        }
        status = [state for key, state in sensors.items() if key.endswith("_server_status")]
        counts = [
            state
            for key, state in sensors.items()
            if key == f"{entry.entry_id}_model_count"
        ]
        assert len(status) == 1 and status[0].state == "online", sensors
        assert len(counts) == 1 and int(counts[0].state) >= 1, sensors

    check_sensors()
    response = await hass.services.async_call(
        "lemonade", "chat_completion",
        {"entry_id": entry.entry_id, "model": MODEL,
         "prompt": "Say hello briefly. /no_think", "max_tokens": 128},
        blocking=True, return_response=True,
    )
    assert isinstance(response.get("content"), str) and response["content"].strip(), response
    print("Chat response:", json.dumps(response))

    # Home Assistant's local date/time intents return native temporal objects.
    # Exercise the real conversion and Lemonade transport path so those values
    # cannot regress to stdlib json.dumps failures in Assist tool history.
    from homeassistant.components.conversation import ToolResultContent

    from custom_components.lemonade.chat import content_to_message

    temporal_tool_message = content_to_message(
        ToolResultContent(
            agent_id="conversation.lemonade_e2e",
            tool_call_id="call-time",
            tool_name="GetCurrentTime",
            tool_result={
                "speech_slots": {"time": datetime.time(7, 30)},
                "date": datetime.date(2026, 9, 16),
                "timestamp": datetime.datetime(
                    2026, 9, 16, 12, 0, tzinfo=datetime.UTC
                ),
            },
        )
    )
    assert json.loads(temporal_tool_message["content"]) == {
        "speech_slots": {"time": "07:30:00"},
        "date": "2026-09-16",
        "timestamp": "2026-09-16T12:00:00+00:00",
    }, temporal_tool_message
    temporal_response = await entry.runtime_data.client.chat_completion(
        model=MODEL,
        messages=[
            {"role": "user", "content": "What time is it?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-time",
                        "type": "function",
                        "function": {
                            "name": "GetCurrentTime",
                            "arguments": "{}",
                        },
                    }
                ],
            },
            temporal_tool_message,
            {"role": "user", "content": "Reply briefly. /no_think"},
        ],
        max_tokens=128,
    )
    assert temporal_response.get("choices"), temporal_response
    print("Temporal tool result response:", json.dumps(temporal_response))

    # Exercise the actual Assist conversation pipeline, including its streamed
    # chat completion path. The starter profile creates the agent entity.
    registry = er.async_get(hass)
    agents = [
        item.entity_id
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.domain == "conversation"
    ]
    assert agents, "Conversation profile entity was not created"
    assist = await hass.services.async_call(
        "conversation", "process",
        {"agent_id": agents[0], "text": "Say hello briefly. /no_think"},
        blocking=True, return_response=True,
    )
    speech = (
        assist.get("response", {})
        .get("speech", {})
        .get("plain", {})
        .get("speech", "")
        if isinstance(assist, dict) else ""
    )
    assert isinstance(speech, str) and speech.strip(), assist
    print("Assist response:", json.dumps(assist))
    assert await hass.config_entries.async_reload(entry.entry_id), "Reload failed"
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED, entry.state
    check_sensors()
    assert await hass.config_entries.async_unload(entry.entry_id), "Unload failed"
    assert entry.entry_id not in hass.data.get("lemonade", {}), "Runtime leaked"
    print(
        "PASS: config flow, setup, sensors, CPU chat inference, temporal tool "
        "results, streamed Assist, reload, unload"
    )


async def main():
    print(f"Home Assistant {__version__}; model {MODEL}")
    await prepare_server()
    hass = HomeAssistant("/config")
    try:
        async with asyncio.timeout(600):
            await exercise(hass)
    finally:
        await hass.async_stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
