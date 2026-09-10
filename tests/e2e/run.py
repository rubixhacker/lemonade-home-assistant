"""Exercise the real HA runtime against a real Lemonade container, without mocks."""

import asyncio
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
        status = [state for key, state in sensors.items() if key == f"{entry.entry_id}_server_status"]
        counts = [state for key, state in sensors.items() if key == f"{entry.entry_id}_model_count"]
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
    assert await hass.config_entries.async_reload(entry.entry_id), "Reload failed"
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED, entry.state
    check_sensors()
    assert await hass.config_entries.async_unload(entry.entry_id), "Unload failed"
    assert entry.entry_id not in hass.data.get("lemonade", {}), "Runtime leaked"
    print("PASS: config flow, setup, sensors, CPU chat inference, reload, unload")


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
