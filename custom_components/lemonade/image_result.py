"""Shared Lemonade image generation response decoding."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from homeassistant.exceptions import HomeAssistantError

DEFAULT_IMAGE_MIME_TYPE = "image/png"
DEFAULT_IMAGE_EXTENSION = "png"
AI_TASK_NO_IMAGE_ERROR = "No image returned"
DIRECT_SERVICE_SAVE_NO_IMAGE_ERROR = (
    "Lemonade image response did not contain image bytes to save"
)

_IMAGE_VALUE_KEYS = ("b64_json", "url", "image")
_SAFE_EXTENSION = re.compile(r"[^A-Za-z0-9._-]+")
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")
_MEDIA_SOURCE_PREFIX = "media-source://media_source/local/lemonade"


@dataclass(frozen=True)
class LemonadeImageResult:
    """Decoded Lemonade image generation result."""

    image_bytes: bytes
    mime_type: str
    extension: str


@dataclass(frozen=True)
class GeneratedImageArtifact:
    """Image bytes and Lemonade media artifact metadata ready to save."""

    image_bytes: bytes
    mime_type: str
    extension: str
    filename: str
    media_path: str


@dataclass(frozen=True)
class ImageGenerationRequest:
    """Typed Lemonade image generation invocation."""

    prompt: str
    model: str
    size: str | None = None

    def client_kwargs(self) -> dict[str, Any]:
        """Return Lemonade client arguments without empty optional values."""
        kwargs: dict[str, Any] = {
            "prompt": self.prompt,
            "model": self.model,
        }
        if self.size:
            kwargs["size"] = self.size
        return kwargs


@dataclass(frozen=True)
class ImageGenerationResult:
    """Raw and decoded Lemonade image generation response."""

    response: Any
    image_result: LemonadeImageResult | None

    def require_image(
        self,
        error_message: str = AI_TASK_NO_IMAGE_ERROR,
    ) -> LemonadeImageResult:
        """Return decoded image data or raise the module-owned no-image error."""
        if self.image_result is None:
            raise HomeAssistantError(error_message)
        return self.image_result

    def artifact(
        self,
        requested_filename: Any = None,
        *,
        timestamp_slug: str | None = None,
    ) -> GeneratedImageArtifact | None:
        """Return media artifact metadata for the decoded image, if present."""
        if self.image_result is None:
            return None
        return _generated_image_artifact_from_result(
            self.image_result,
            requested_filename,
            timestamp_slug=timestamp_slug,
        )

    def require_artifact(
        self,
        requested_filename: Any = None,
        *,
        timestamp_slug: str | None = None,
        error_message: str = DIRECT_SERVICE_SAVE_NO_IMAGE_ERROR,
    ) -> GeneratedImageArtifact:
        """Return media artifact metadata or raise the direct-service save error."""
        artifact = self.artifact(
            requested_filename,
            timestamp_slug=timestamp_slug,
        )
        if artifact is None:
            raise HomeAssistantError(error_message)
        return artifact


async def generate_image(
    client: Any,
    request: ImageGenerationRequest,
) -> ImageGenerationResult:
    """Invoke Lemonade image generation and decode the first returned image."""
    response = await client.generate_image(**request.client_kwargs())
    return ImageGenerationResult(
        response=response,
        image_result=decode_image_result(response),
    )


def extension_from_mime_type(mime_type: str) -> str:
    """Return a safe file extension for an image MIME type."""
    subtype = mime_type.partition("/")[2].split(";", 1)[0].strip().lower()
    if subtype == "jpeg":
        return "jpg"
    subtype = subtype.split("+", 1)[0]
    return _SAFE_EXTENSION.sub("_", subtype).strip("._") or DEFAULT_IMAGE_EXTENSION


def decode_image_result(response: Any) -> LemonadeImageResult | None:
    """Decode the first image payload from an OpenAI/Lemonade response."""
    for value in _image_response_values(response):
        result = decode_image_value(value)
        if result is not None:
            return result
    return None


def decode_image_value(value: Any) -> LemonadeImageResult | None:
    """Decode one image value that may be raw bytes, base64, or a data URL."""
    if isinstance(value, bytes):
        return LemonadeImageResult(
            image_bytes=value,
            mime_type=DEFAULT_IMAGE_MIME_TYPE,
            extension=DEFAULT_IMAGE_EXTENSION,
        )
    if not isinstance(value, str) or not value:
        return None

    data_url_result = _decode_data_image_url(value)
    if data_url_result is not None:
        return data_url_result

    image_bytes = _decode_base64(value)
    if image_bytes is None:
        return None
    return LemonadeImageResult(
        image_bytes=image_bytes,
        mime_type=DEFAULT_IMAGE_MIME_TYPE,
        extension=DEFAULT_IMAGE_EXTENSION,
    )


def image_bytes_and_extension(response: Any) -> tuple[bytes | None, str | None]:
    """Return decoded image bytes and extension for service compatibility."""
    result = decode_image_result(response)
    if result is None:
        return None, None
    return result.image_bytes, result.extension


def generated_image_artifact(
    response: Any,
    requested_filename: Any = None,
    *,
    timestamp_slug: str | None = None,
) -> GeneratedImageArtifact | None:
    """Return decoded image bytes plus media-save artifact semantics."""
    result = decode_image_result(response)
    if result is None:
        return None

    return _generated_image_artifact_from_result(
        result,
        requested_filename,
        timestamp_slug=timestamp_slug,
    )


def _generated_image_artifact_from_result(
    result: LemonadeImageResult,
    requested_filename: Any = None,
    *,
    timestamp_slug: str | None = None,
) -> GeneratedImageArtifact:
    """Return media-save artifact metadata for a decoded image result."""
    extension = result.extension or DEFAULT_IMAGE_EXTENSION
    default_filename = f"lemonade_{timestamp_slug or _utcnow_slug()}.{extension}"
    filename = safe_media_filename(requested_filename, default_filename)
    return GeneratedImageArtifact(
        image_bytes=result.image_bytes,
        mime_type=result.mime_type,
        extension=extension,
        filename=filename,
        media_path=f"{_MEDIA_SOURCE_PREFIX}/{filename}",
    )


def safe_media_filename(filename: Any, default_filename: str) -> str:
    """Return a filename safe to place under the Lemonade media directory."""
    if not isinstance(filename, str) or not filename.strip():
        return default_filename

    basename = Path(filename.replace("\\", "/")).name
    basename = _SAFE_FILENAME.sub("_", basename).strip("._")
    if not basename or basename in {".", ".."}:
        return default_filename
    return basename


def _utcnow_slug() -> str:
    """Return a UTC timestamp slug for generated media filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _image_response_values(response: Any) -> Iterator[Any]:
    """Yield image payload candidates from an OpenAI/Lemonade response."""
    if isinstance(response, Mapping):
        data = response.get("data")
        if isinstance(data, list):
            for item in data:
                yield from _image_response_values(item)
        for key in _IMAGE_VALUE_KEYS:
            if key in response:
                yield response[key]
        return

    if isinstance(response, list):
        for item in response:
            yield from _image_response_values(item)
        return

    yielded_attribute = False
    data = getattr(response, "data", None)
    if isinstance(data, list):
        yielded_attribute = True
        for item in data:
            yield from _image_response_values(item)

    for key in _IMAGE_VALUE_KEYS:
        if hasattr(response, key):
            yielded_attribute = True
            yield getattr(response, key)

    if not yielded_attribute:
        yield response


def _decode_data_image_url(value: str) -> LemonadeImageResult | None:
    """Decode a base64 data:image URL."""
    if value[:5].lower() != "data:":
        return None

    metadata, separator, encoded = value.partition(",")
    if not separator:
        return None

    metadata_lower = metadata.lower()
    if not metadata_lower.startswith("data:image/") or ";base64" not in metadata_lower:
        return None

    media_type = metadata[5:].split(";", 1)[0].strip().lower()
    image_bytes = _decode_base64(encoded)
    if image_bytes is None:
        return None

    return LemonadeImageResult(
        image_bytes=image_bytes,
        mime_type=media_type or DEFAULT_IMAGE_MIME_TYPE,
        extension=extension_from_mime_type(media_type),
    )


def _decode_base64(value: str) -> bytes | None:
    """Decode strict base64 bytes."""
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None
