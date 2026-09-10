"""Home Assistant end-to-end test fixtures."""

from collections.abc import AsyncIterator
import json
from typing import Any

from aiohttp import web
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component
import pytest

from custom_components.lemonade.const import DOMAIN


MODELS = (
    {
        "id": "local-chat",
        "recipe": "llamacpp",
        "labels": ["tool-calling"],
        "downloaded": True,
    },
    {
        "id": "house-router",
        "recipe": "router",
        "labels": [],
        "downloaded": True,
    },
    {
        "id": "house-omni",
        "recipe": "omni",
        "labels": [],
        "downloaded": True,
    },
    {
        "id": "intent-classifier",
        "recipe": "transformers",
        "labels": ["classification"],
        "downloaded": True,
    },
    {
        "id": "kokoro-v1",
        "recipe": "tts",
        "labels": ["tts"],
        "downloaded": True,
    },
    {
        "id": "Whisper-Base",
        "recipe": "whispercpp",
        "labels": ["stt"],
        "downloaded": True,
    },
)


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load the integration from this checkout."""


@pytest.fixture
async def lemonade_server(
    aiohttp_server: Any,
    socket_enabled: None,
) -> AsyncIterator[tuple[str, list[dict[str, Any]]]]:
    """Run a real HTTP fake at the Lemonade Server boundary."""
    requests: list[dict[str, Any]] = []
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "version": "11.5.0"})

    async def models(_: web.Request) -> web.Response:
        return web.json_response({"data": MODELS})

    async def chat(request: web.Request) -> web.Response:
        payload = await request.json()
        requests.append({"path": request.path, "payload": payload})
        if payload.get("stream"):
            response = web.StreamResponse(
                status=200,
                headers={"Content-Type": "text/event-stream"},
            )
            await response.prepare(request)
            for index, content in enumerate(("Lemonade end-to-end ", "response")):
                delta = {"content": content}
                if index == 0:
                    delta["role"] = "assistant"
                await response.write(
                    ("data: " + json.dumps({
                        "model": payload["model"],
                        "choices": [{"delta": delta}],
                    }) + "\n\n").encode()
                )
            await response.write(b"data: [DONE]\n\n")
            await response.write_eof()
            return response
        response: dict[str, Any] = {
            "model": payload["model"],
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Lemonade end-to-end response",
                    }
                }
            ],
        }
        if payload.get("route_trace"):
            response["route_decision"] = {
                "selected_model": "local-chat",
                "reason": "local candidate",
            }
        return web.json_response(response)

    async def classify(request: web.Request) -> web.Response:
        payload = await request.json()
        requests.append({"path": request.path, "payload": payload})
        return web.json_response(
            {
                "model": payload["model"],
                "labels": {"automation": 0.91, "conversation": 0.09},
            }
        )

    async def text_to_speech(request: web.Request) -> web.Response:
        payload = await request.json()
        requests.append({"path": request.path, "payload": payload})
        return web.Response(body=b"voice-bytes", content_type="audio/mpeg")

    async def transcribe(request: web.Request) -> web.Response:
        fields = await request.post()
        requests.append({"path": request.path, "payload": {
            "model": fields.get("model"), "language": fields.get("language"),
        }})
        return web.json_response({"text": "bonjour"})

    app.router.add_post("/v1/audio/transcriptions", transcribe)
    app.router.add_get("/v1/health", health)
    app.router.add_get("/v1/models", models)
    app.router.add_post("/v1/chat/completions", chat)
    app.router.add_post("/v1/classify", classify)
    app.router.add_post("/v1/audio/speech", text_to_speech)
    app.router.add_get("/replacement/v1/health", health)
    app.router.add_get("/replacement/v1/models", models)
    app.router.add_post("/replacement/v1/chat/completions", chat)
    app.router.add_post("/replacement/v1/classify", classify)
    app.router.add_post("/replacement/v1/audio/speech", text_to_speech)
    server = await aiohttp_server(app)
    yield str(server.make_url("")).rstrip("/"), requests


@pytest.fixture
async def lemonade_entry(
    hass: HomeAssistant,
    lemonade_server: tuple[str, list[dict[str, Any]]],
) -> tuple[Any, str, list[dict[str, Any]]]:
    """Create and load a Server Entry through Home Assistant's public flow."""
    server_url, requests = lemonade_server
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
    await hass.async_block_till_done()
    entry = result["result"]
    assert entry.state is config_entries.ConfigEntryState.LOADED
    return entry, server_url, requests
