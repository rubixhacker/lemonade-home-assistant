"""Bounded, user-initiated Lemonade Server beacon discovery."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network, ip_address, ip_network
import json
import logging
import socket
from typing import Any
from urllib.parse import urlsplit, urlunsplit

_LOGGER = logging.getLogger(__name__)

BEACON_PORT = 13305
DEFAULT_DISCOVERY_SECONDS = 3.0
_BEACON_API_PATH = "/api/v1/"
_SCAN_TASK_LOCK = asyncio.Lock()
_ACTIVE_SCAN_TASK: asyncio.Task[dict[str, DiscoveredServer]] | None = None


@dataclass(frozen=True)
class DiscoveredServer:
    """A safe but not yet connection-validated Server Entry candidate."""

    endpoint: str
    hostname: str

    @property
    def title(self) -> str:
        """Return the editable display suggestion for this candidate."""
        return f"Lemonade Server \u2014 {self.hostname}"


def enabled_ipv4_networks(
    adapters: Iterable[Mapping[str, Any]],
) -> tuple[IPv4Network, ...]:
    """Return enabled, directly connected IPv4 networks."""
    networks: set[IPv4Network] = set()
    for adapter in adapters:
        if not adapter.get("enabled"):
            continue
        for ip_info in adapter.get("ipv4", ()):
            if not isinstance(ip_info, Mapping):
                continue
            address = ip_info.get("address")
            prefix = ip_info.get("network_prefix")
            try:
                network = ip_network(f"{address}/{prefix}", strict=False)
            except ValueError:
                continue
            if isinstance(network, IPv4Network):
                networks.add(network)
    return tuple(
        sorted(
            networks,
            key=lambda item: (int(item.network_address), item.prefixlen),
        )
    )


def _eligible_source(
    source: IPv4Address,
    allowed_networks: Iterable[IPv4Network],
) -> bool:
    """Return whether a packet source belongs to an enabled local adapter."""
    return source.is_loopback or any(source in network for network in allowed_networks)


def _normalize_beacon_url(value: Any, source: IPv4Address) -> str | None:
    """Normalize the upstream beacon URL to a client Server Endpoint."""
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        advertised_host = ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not isinstance(advertised_host, IPv4Address)
        or advertised_host != source
        or port is None
        or not 1 <= port <= 65535
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path.rstrip("/") != _BEACON_API_PATH.rstrip("/")
        or parsed.query
        or parsed.fragment
    ):
        return None
    return urlunsplit((parsed.scheme, f"{advertised_host}:{port}", "", "", ""))


def parse_server_beacon(
    payload: bytes,
    source_host: str,
    allowed_networks: Iterable[IPv4Network],
) -> DiscoveredServer | None:
    """Parse a UDP payload into a safe Discovered Server candidate."""
    try:
        source = ip_address(source_host)
        data = json.loads(payload)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(source, IPv4Address) or not _eligible_source(
        source, allowed_networks
    ):
        return None
    if not isinstance(data, dict) or data.get("service") != "lemonade":
        return None

    hostname = data.get("hostname")
    if not isinstance(hostname, str):
        return None
    hostname = hostname.strip()
    if (
        not hostname
        or len(hostname) > 253
        or any(
            character.isspace() or not character.isprintable()
            for character in hostname
        )
    ):
        return None

    endpoint = _normalize_beacon_url(data.get("url"), source)
    if endpoint is None:
        return None
    return DiscoveredServer(endpoint=endpoint, hostname=hostname)


class _BeaconProtocol(asyncio.DatagramProtocol):
    """Collect valid beacons during one bounded scan."""

    def __init__(
        self,
        allowed_networks: tuple[IPv4Network, ...],
        candidates: dict[str, DiscoveredServer],
    ) -> None:
        self._allowed_networks = allowed_networks
        self._candidates = candidates

    def datagram_received(self, data: bytes, addr: tuple[Any, ...]) -> None:
        """Parse and deduplicate one received UDP datagram."""
        if not addr or not isinstance(addr[0], str):
            return
        candidate = parse_server_beacon(data, addr[0], self._allowed_networks)
        if candidate is not None:
            self._candidates.setdefault(candidate.endpoint, candidate)


async def _async_collect_server_beacons(
    allowed_networks: Iterable[IPv4Network],
    *,
    duration: float,
) -> dict[str, DiscoveredServer]:
    """Collect one scan's beacons, releasing the socket when done."""
    networks = tuple(allowed_networks)
    candidates: dict[str, DiscoveredServer] = {}
    loop = asyncio.get_running_loop()
    try:
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _BeaconProtocol(networks, candidates),
            local_addr=("0.0.0.0", BEACON_PORT),
            family=socket.AF_INET,
        )
    except OSError as err:
        _LOGGER.debug("Unable to listen for Lemonade Server beacons: %s", err)
        return {}
    try:
        await asyncio.sleep(max(0.0, duration))
    finally:
        transport.close()
    return candidates


def _clear_active_scan(task: asyncio.Task[dict[str, DiscoveredServer]]) -> None:
    """Release completed shared scan results instead of caching candidates."""
    global _ACTIVE_SCAN_TASK
    if _ACTIVE_SCAN_TASK is task:
        _ACTIVE_SCAN_TASK = None


async def async_scan_server_beacons(
    allowed_networks: Iterable[IPv4Network],
    *,
    duration: float = DEFAULT_DISCOVERY_SECONDS,
) -> dict[str, DiscoveredServer]:
    """Share one bounded passive scan among concurrent setup flows."""
    global _ACTIVE_SCAN_TASK
    async with _SCAN_TASK_LOCK:
        if _ACTIVE_SCAN_TASK is None:
            _ACTIVE_SCAN_TASK = asyncio.create_task(
                _async_collect_server_beacons(
                    tuple(allowed_networks),
                    duration=duration,
                )
            )
            _ACTIVE_SCAN_TASK.add_done_callback(_clear_active_scan)
        scan_task = _ACTIVE_SCAN_TASK
    return dict(await asyncio.shield(scan_task))
