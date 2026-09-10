"""Async client for Lemonade Server's OpenAI-compatible API."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import aiohttp

from .const import (
    DEFAULT_INFERENCE_TIMEOUT,
    DEFAULT_TIMEOUT,
    ENDPOINT_AUDIO_SPEECH,
    ENDPOINT_CLASSIFY_TEXT,
    ENDPOINT_AUDIO_TRANSCRIPTIONS,
    ENDPOINT_CHAT,
    ENDPOINT_HEALTH,
    ENDPOINT_IMAGES_GENERATIONS,
    ENDPOINT_MODELS,
)


class LemonadeError(Exception):
    """Base Lemonade API error."""


class LemonadeAuthError(LemonadeError):
    """Lemonade API authentication error."""


class LemonadeClient:
    """Small async Lemonade Server API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        inference_timeout: float = DEFAULT_INFERENCE_TIMEOUT,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the client."""
        self.session = session
        self.url = url.rstrip("/")
        self.api_key = api_key.strip() if api_key else None
        self.timeout = timeout
        self.inference_timeout = inference_timeout
        self.verify_ssl = verify_ssl

    @property
    def headers(self) -> dict[str, str]:
        """Return request headers."""
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request_json_payload(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        """Request raw JSON from Lemonade Server."""
        return await self._request(
            method,
            path,
            self._read_json_response,
            **kwargs,
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Request JSON from Lemonade Server."""
        data = await self._request_json_payload(method, path, **kwargs)
        if isinstance(data, dict):
            return data
        return {"data": data}

    async def _request_bytes(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[bytes, str | None]:
        """Request bytes from Lemonade Server."""
        return await self._request(
            method,
            path,
            self._read_bytes_response,
            **kwargs,
        )

    async def _request(
        self,
        method: str,
        path: str,
        read_response: Callable[[aiohttp.ClientResponse], Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        """Request data from Lemonade Server and classify response status."""
        request_timeout = kwargs.pop("request_timeout", self.timeout)
        request_kwargs = dict(kwargs)
        request_kwargs["timeout"] = aiohttp.ClientTimeout(total=request_timeout)
        if not self.verify_ssl:
            request_kwargs["ssl"] = False

        async with asyncio.timeout(request_timeout):
            async with self.session.request(
                method,
                f"{self.url}{path}",
                headers=self.headers,
                **request_kwargs,
            ) as response:
                await self._raise_for_response_status(response)
                return await read_response(response)

    async def _raise_for_response_status(
        self,
        response: aiohttp.ClientResponse,
    ) -> None:
        """Raise a Lemonade error for unsuccessful response status."""
        if response.status in (401, 403):
            raise LemonadeAuthError("Invalid Lemonade Server credentials")
        if response.status >= 400:
            body = await response.text()
            raise LemonadeError(
                f"Lemonade Server returned HTTP {response.status}: {body}"
            )

    async def _read_json_response(self, response: aiohttp.ClientResponse) -> Any:
        """Read a JSON response without content type enforcement."""
        return await response.json(content_type=None)

    async def _read_bytes_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> tuple[bytes, str | None]:
        """Read a binary response and content type."""
        return await response.read(), response.headers.get("Content-Type")

    async def health(self) -> dict[str, Any]:
        """Return Lemonade Server health."""
        return await self._request_json("GET", ENDPOINT_HEALTH)

    async def models(self) -> dict[str, Any] | list[Any]:
        """Return available Lemonade models."""
        return await self._request_json_payload("GET", ENDPOINT_MODELS)

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        keep_alive: int | None = None,
        route_trace: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a chat completion."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if response_format is not None:
            payload["response_format"] = response_format
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        if route_trace is not None:
            payload["route_trace"] = route_trace
        if metadata is not None:
            payload["metadata"] = metadata
        return await self._request_json(
            "POST", ENDPOINT_CHAT, json=payload, request_timeout=self.inference_timeout
        )

    async def stream_chat_completion(
        self, *, model: str, messages: list[dict[str, Any]], **options: Any
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield decoded Server-Sent Events from a streaming chat completion."""
        options.pop("stream", None)
        payload = {"model": model, "messages": messages, "stream": True, **options}
        request_kwargs: dict[str, Any] = {"json": payload}
        request_kwargs["timeout"] = aiohttp.ClientTimeout(total=self.inference_timeout)
        if not self.verify_ssl:
            request_kwargs["ssl"] = False
        async with asyncio.timeout(self.inference_timeout):
            completed = False
            async with self.session.request(
                "POST",
                f"{self.url}{ENDPOINT_CHAT}",
                headers=self.headers,
                **request_kwargs,
            ) as response:
                await self._raise_for_response_status(response)
                async for line in response.content:
                    line = line.strip()
                    if not line or not line.startswith(b"data:"):
                        continue
                    data = line[5:].strip()
                    if data == b"[DONE]":
                        completed = True
                        return
                    try:
                        decoded = json.loads(data)
                    except json.JSONDecodeError as err:
                        raise LemonadeError(
                            "Invalid streaming response from Lemonade Server"
                        ) from err
                    if isinstance(decoded, dict):
                        if "error" in decoded:
                            raise LemonadeError(
                                f"Lemonade Server streaming error: {decoded['error']}"
                            )
                        yield decoded
            if not completed:
                raise LemonadeError(
                    "Lemonade Server streaming response ended before [DONE]"
                )

    def chat_completion_stream(
        self, *, model: str, messages: list[dict[str, Any]], **options: Any
    ) -> AsyncIterator[dict[str, Any]]:
        """Return the streaming chat iterator using the adapter naming convention."""
        return self.stream_chat_completion(
            model=model, messages=messages, **options
        )

    async def generate_image(
        self,
        *,
        prompt: str,
        model: str | None = None,
        size: str | None = None,
    ) -> dict[str, Any]:
        """Generate an image."""
        payload: dict[str, Any] = {"prompt": prompt}
        if model:
            payload["model"] = model
        if size:
            payload["size"] = size
        return await self._request_json(
            "POST",
            ENDPOINT_IMAGES_GENERATIONS,
            json=payload,
            request_timeout=self.inference_timeout,
        )

    async def text_to_speech(
        self,
        *,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        response_format: str | None = None,
        lang_code: str | None = None,
        speed: float | None = None,
    ) -> tuple[bytes, str | None]:
        """Convert text to speech and return audio bytes."""
        payload: dict[str, Any] = {"input": text}
        if model:
            payload["model"] = model
        if voice:
            payload["voice"] = voice
        if response_format:
            payload["response_format"] = response_format
        if lang_code:
            payload["lang_code"] = lang_code
        if speed is not None:
            payload["speed"] = speed
        return await self._request_bytes(
            "POST",
            ENDPOINT_AUDIO_SPEECH,
            json=payload,
            request_timeout=self.inference_timeout,
        )

    async def transcribe_audio(
        self,
        *,
        audio: bytes,
        filename: str,
        model: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Transcribe audio bytes."""
        form = aiohttp.FormData()
        form.add_field(
            "file",
            audio,
            filename=filename,
            content_type="application/octet-stream",
        )
        if model:
            form.add_field("model", model)
        if language:
            form.add_field("language", language)
        return await self._request_json(
            "POST",
            ENDPOINT_AUDIO_TRANSCRIPTIONS,
            data=form,
            request_timeout=self.inference_timeout,
        )

    async def classify_text(
        self,
        *,
        text: str,
        model: str,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """Classify text with a Lemonade encoder model."""
        payload: dict[str, Any] = {"text": text, "model": model}
        if top_k is not None:
            payload["top_k"] = top_k
        return await self._request_json(
            "POST",
            ENDPOINT_CLASSIFY_TEXT,
            json=payload,
            request_timeout=self.inference_timeout,
        )
