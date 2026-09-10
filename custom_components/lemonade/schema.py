"""Convert HA schemas across legacy and Probatio serializer contracts."""

from typing import Any

import voluptuous_openapi

try:
    from probatio import UNSUPPORTED as PROBATIO_UNSUPPORTED
except ImportError:  # Older Home Assistant releases do not use Probatio.
    PROBATIO_UNSUPPORTED = None


def convert(schema: Any, *, custom_serializer: Any = None) -> dict[str, Any]:
    """Translate the serializer's defer sentinel before legacy conversion."""
    serializer = custom_serializer
    if PROBATIO_UNSUPPORTED is not None and callable(custom_serializer):
        def serializer(value: Any) -> Any:
            result = custom_serializer(value)
            if result is PROBATIO_UNSUPPORTED:
                return voluptuous_openapi.UNSUPPORTED
            return result

    return voluptuous_openapi.convert(schema, custom_serializer=serializer)
