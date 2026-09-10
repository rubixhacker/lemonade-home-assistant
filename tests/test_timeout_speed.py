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


class _StreamResponse(_Response):
    def __init__(self, lines):
        self.content = _Lines(lines)


class _Lines:
    def __init__(self, lines):
        self.lines = iter(lines)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.lines)
        except StopIteration as err:
            raise StopAsyncIteration from err


class _StreamSession(_Session):
    def __init__(self, lines):
        super().__init__()
        self.lines = lines

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return _StreamResponse(self.lines)


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


@pytest.mark.asyncio
async def test_sse_requires_done_and_rejects_error_envelope():
    for lines, expected in (
        ([b'data: {"choices": []}\n'], r"ended before \[DONE\]"),
        ([b'data: {"error": "overloaded"}\n'], "streaming error"),
    ):
        client = LemonadeClient(_StreamSession(lines), "http://server")
        with pytest.raises(LemonadeError, match=expected):
            [chunk async for chunk in client.stream_chat_completion(model="m", messages=[])]


@pytest.mark.asyncio
async def test_sse_done_yields_chunk():
    client = LemonadeClient(
        _StreamSession([b'data: {"choices": []}\n', b"data: [DONE]\n"]),
        "http://server",
    )
    assert [chunk async for chunk in client.stream_chat_completion(model="m", messages=[])] == [{"choices": []}]
