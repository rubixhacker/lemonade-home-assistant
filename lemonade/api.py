"""Async client for Lemonade Server's OpenAI-compatible API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import (
    ENDPOINT_AUDIO_SPEECH,
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
        timeout: float = 30.0,
    ) -> None:
        """Initialize the client."""
        self.session = session
        self.url = url.rstrip("/")
        self.api_key = api_key.strip() if api_key else None
        self.timeout = timeout

    @property
    def headers(self) -> dict[str, str]:
        """Return request headers."""
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request_json(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Request JSON from Lemonade Server."""
        async with asyncio.timeout(self.timeout):
            async with self.session.request(
                method,
                f"{self.url}{path}",
                headers=self.headers,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise LemonadeAuthError("Invalid Lemonade Server credentials")
                if response.status >= 400:
                    body = await response.text()
                    raise LemonadeError(
                        f"Lemonade Server returned HTTP {response.status}: {body}"
                    )
                data = await response.json(content_type=None)
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
        async with asyncio.timeout(self.timeout):
            async with self.session.request(
                method,
                f"{self.url}{path}",
                headers=self.headers,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise LemonadeAuthError("Invalid Lemonade Server credentials")
                if response.status >= 400:
                    body = await response.text()
                    raise LemonadeError(
                        f"Lemonade Server returned HTTP {response.status}: {body}"
                    )
                return await response.read(), response.headers.get("Content-Type")

    async def health(self) -> dict[str, Any]:
        """Return Lemonade Server health."""
        return await self._request_json("GET", ENDPOINT_HEALTH)

    async def models(self) -> dict[str, Any]:
        """Return available Lemonade models."""
        return await self._request_json("GET", ENDPOINT_MODELS)

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
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
        return await self._request_json("POST", ENDPOINT_CHAT, json=payload)

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
        return await self._request_json("POST", ENDPOINT_IMAGES_GENERATIONS, json=payload)

    async def text_to_speech(
        self,
        *,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        response_format: str | None = None,
    ) -> tuple[bytes, str | None]:
        """Convert text to speech and return audio bytes."""
        payload: dict[str, Any] = {"input": text}
        if model:
            payload["model"] = model
        if voice:
            payload["voice"] = voice
        if response_format:
            payload["response_format"] = response_format
        return await self._request_bytes("POST", ENDPOINT_AUDIO_SPEECH, json=payload)

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
        return await self._request_json("POST", ENDPOINT_AUDIO_TRANSCRIPTIONS, data=form)
