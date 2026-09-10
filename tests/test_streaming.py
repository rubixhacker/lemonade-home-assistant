"""Focused tests for Lemonade Assist streaming."""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))
# Install the lightweight Home Assistant modules used by the repository tests.
import test_runtime  # noqa: F401

from lemonade.chat import ChatTurnRequest, async_execute_chat_turn
from homeassistant.exceptions import HomeAssistantError


class _ChatLog:
    def __init__(self) -> None:
        self.content = []
        self.llm_api = None
        self.unresponded_tool_results = []
        self.deltas = []

    async def async_add_delta_content_stream(self, _agent: str, stream):
        async for delta in stream:
            self.deltas.append(delta)


class _Stream:
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.chunks:
            raise StopAsyncIteration
        return self.chunks.pop(0)

    async def aclose(self):
        self.closed = True


class _GatedStream(_Stream):
    def __init__(self, chunks):
        super().__init__(chunks)
        self.first_seen = asyncio.Event()
        self.release = asyncio.Event()

    async def __anext__(self):
        if self.first_seen.is_set():
            await self.release.wait()
        value = await super().__anext__()
        if not self.first_seen.is_set():
            self.first_seen.set()
        return value


class _Client:
    def __init__(self, stream):
        self.stream = stream

    def chat_completion_stream(self, **_kwargs):
        return self.stream


class StreamingTest(unittest.IsolatedAsyncioTestCase):
    async def test_first_text_is_visible_before_stream_finishes_and_cancel_closes(self):
        stream = _GatedStream([
            {"choices": [{"delta": {"content": "Hello"}}]},
        ])
        chat_log = _ChatLog()
        task = asyncio.create_task(async_execute_chat_turn(ChatTurnRequest(
            entity_id="conversation.test", client=_Client(stream), model="m",
            chat_log=chat_log, stream=True,
        )))
        await asyncio.wait_for(stream.first_seen.wait(), 1)
        # The transport is still waiting for its next event, while HA already
        # received the first text delta through the live ChatLog stream.
        self.assertEqual([{"content": "Hello"}], chat_log.deltas)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(stream.closed)

    async def test_rejects_malformed_tool_arguments_after_done(self):
        stream = _Stream([
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call-1", "function": {"name": "turn_on", "arguments": '{"entity":'}}]}}]},
        ])
        with self.assertRaises(HomeAssistantError):
            await async_execute_chat_turn(ChatTurnRequest(
                entity_id="conversation.test", client=_Client(stream), model="m",
                chat_log=_ChatLog(), stream=True,
            ))

    async def test_rejects_length_terminated_tool_call(self):
        stream = _Stream([
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"name": "turn_on", "arguments": "{}"}}]}, "finish_reason": "length"}]},
        ])
        with self.assertRaises(HomeAssistantError):
            await async_execute_chat_turn(ChatTurnRequest(
                entity_id="conversation.test", client=_Client(stream), model="m",
                chat_log=_ChatLog(), stream=True,
            ))

    async def test_forwards_text_chunks_and_closes_sse(self):
        stream = _Stream([
            {"choices": [{"delta": {"content": "Hel"}}]},
            {"choices": [{"delta": {"content": "lo"}}]},
            {"choices": [{"delta": {}, "finish_reason": "stop"}]},
        ])
        chat_log = _ChatLog()
        outcome = await async_execute_chat_turn(ChatTurnRequest(
            entity_id="conversation.test", client=_Client(stream), model="m",
            chat_log=chat_log, stream=True,
        ))
        self.assertEqual(
            [{"content": "Hel"}, {"content": "lo"}],
            chat_log.deltas,
        )
        self.assertEqual("Hello", outcome.final_assistant_content)
        self.assertTrue(stream.closed)

    async def test_assembles_fragmented_tool_call(self):
        stream = _Stream([
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call-1", "function": {"name": "turn_on", "arguments": '{"entity": '}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "\"light.kitchen\"}"}}]}}]},
        ])
        chat_log = _ChatLog()
        await async_execute_chat_turn(ChatTurnRequest(
            entity_id="conversation.test", client=_Client(stream), model="m",
            chat_log=chat_log, stream=True,
        ))
        self.assertEqual("turn_on", chat_log.deltas[0]["tool_calls"][0].tool_name)
        self.assertEqual({"entity": "light.kitchen"}, chat_log.deltas[0]["tool_calls"][0].tool_args)

    async def test_assembles_multiple_tool_calls_by_index(self):
        stream = _Stream([
            {"choices": [{"delta": {"tool_calls": [
                {"index": 1, "id": "two", "function": {"name": "b", "arguments": "{}"}},
                {"index": 0, "id": "one", "function": {"name": "a", "arguments": "{}"}},
            ]}}]},
        ])
        chat_log = _ChatLog()
        await async_execute_chat_turn(ChatTurnRequest(
            entity_id="conversation.test", client=_Client(stream), model="m",
            chat_log=chat_log, stream=True,
        ))
        calls = chat_log.deltas[0]["tool_calls"]
        self.assertEqual(["one", "two"], [call.id for call in calls])

    async def test_rejects_non_object_tool_arguments_before_chatlog(self):
        from homeassistant.exceptions import HomeAssistantError

        stream = _Stream([
            {"choices": [{"delta": {"tool_calls": [{
                "id": "bad", "function": {"name": "turn_on", "arguments": "[]"}
            }]}}]},
        ])
        chat_log = _ChatLog()
        with self.assertRaises(HomeAssistantError):
            await async_execute_chat_turn(ChatTurnRequest(
                entity_id="conversation.test", client=_Client(stream), model="m",
                chat_log=chat_log, stream=True,
            ))
        self.assertFalse(any("tool_calls" in delta for delta in chat_log.deltas))

    async def test_rejects_length_terminated_tool_call_before_chatlog(self):
        from homeassistant.exceptions import HomeAssistantError

        stream = _Stream([
            {"choices": [{"delta": {"tool_calls": [{
                "id": "short", "function": {"name": "turn_on", "arguments": "{}"}
            }]}}]},
            {"choices": [{"delta": {}, "finish_reason": "length"}]},
        ])
        chat_log = _ChatLog()
        with self.assertRaises(HomeAssistantError):
            await async_execute_chat_turn(ChatTurnRequest(
                entity_id="conversation.test", client=_Client(stream), model="m",
                chat_log=chat_log, stream=True,
            ))
        self.assertFalse(any("tool_calls" in delta for delta in chat_log.deltas))
