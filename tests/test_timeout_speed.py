"""Regression coverage for request budgets and speech speed serialization."""

from __future__ import annotations

import pytest

from custom_components.lemonade.api import LemonadeClient
from custom_components.lemonade.api import LemonadeError
from custom_components.lemonade.const import DEFAULT_INFERENCE_TIMEOUT, DEFAULT_TIMEOUT


class _Response:
    status = 200
    headers = {"Content-Type": "audio/mpeg"}

    async def json(self, content_type=None):
        return {"ok": True}

    async def read(self):
        return b"audio"

    async def text(self):
        return ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class _Session:
    def __init__(self):
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return _Response()








@pytest.mark.asyncio
async def test_health_and_inference_use_separate_transport_budgets():
    session = _Session()
    client = LemonadeClient(session, "http://server")

    await client.health()
    await client.chat_completion(model="model", messages=[])

    assert session.calls[0][2]["timeout"].total == DEFAULT_TIMEOUT
    assert session.calls[1][2]["timeout"].total == DEFAULT_INFERENCE_TIMEOUT


@pytest.mark.asyncio
async def test_tts_speed_is_sent_only_when_requested():
    session = _Session()
    client = LemonadeClient(session, "http://server")

    await client.text_to_speech(text="hello", speed=1.25)

    assert session.calls[-1][2]["json"]["speed"] == 1.25




