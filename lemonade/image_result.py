"""Shared Lemonade image generation response decoding."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
import re
from typing import Any

DEFAULT_IMAGE_MIME_TYPE = "image/png"
DEFAULT_IMAGE_EXTENSION = "png"

_IMAGE_VALUE_KEYS = ("b64_json", "url", "image")
_SAFE_EXTENSION = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class LemonadeImageResult:
    """Decoded Lemonade image generation result."""

    image_bytes: bytes
    mime_type: str
    extension: str


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
