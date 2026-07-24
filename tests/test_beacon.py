"""Tests for user-initiated Lemonade Server beacon discovery."""

from __future__ import annotations

import asyncio
import importlib.util
from ipaddress import ip_network
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

_BEACON_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "lemonade"
    / "beacon.py"
)
_BEACON_SPEC = importlib.util.spec_from_file_location("lemonade_beacon", _BEACON_PATH)
if _BEACON_SPEC is None or _BEACON_SPEC.loader is None:
    raise RuntimeError("Unable to load Lemonade beacon module")
_BEACON = importlib.util.module_from_spec(_BEACON_SPEC)
sys.modules[_BEACON_SPEC.name] = _BEACON
_BEACON_SPEC.loader.exec_module(_BEACON)
DiscoveredServer = _BEACON.DiscoveredServer
async_scan_server_beacons = _BEACON.async_scan_server_beacons
enabled_ipv4_networks = _BEACON.enabled_ipv4_networks
parse_server_beacon = _BEACON.parse_server_beacon


class BeaconParserTest(unittest.TestCase):
    """Specify the safe Server Beacon parsing boundary."""

    def test_valid_current_beacon_is_normalized_to_server_endpoint(self) -> None:
        candidate = parse_server_beacon(
            b'{"service":"lemonade","hostname":"workstation",'
            b'"url":"http://192.168.1.20:8000/api/v1/"}',
            "192.168.1.20",
            (ip_network("192.168.1.0/24"),),
        )

        self.assertEqual(
            DiscoveredServer(
                endpoint="http://192.168.1.20:8000",
                hostname="workstation",
            ),
            candidate,
        )
        self.assertEqual("Lemonade Server \u2014 workstation", candidate.title)

    def test_loopback_beacon_is_eligible(self) -> None:
        candidate = parse_server_beacon(
            b'{"service":"lemonade","hostname":"localhost",'
            b'"url":"http://127.0.0.1:8000/api/v1/"}',
            "127.0.0.1",
            (),
        )

        self.assertEqual("http://127.0.0.1:8000", candidate.endpoint)

    def test_malformed_or_untrusted_beacons_are_rejected(self) -> None:
        cases = (
            (b"not-json", "192.168.1.20"),
            (
                b'{"service":"other","hostname":"workstation",'
                b'"url":"http://192.168.1.20:8000/api/v1/"}',
                "192.168.1.20",
            ),
            (
                b'{"service":"lemonade","hostname":"",'
                b'"url":"http://192.168.1.20:8000/api/v1/"}',
                "192.168.1.20",
            ),
            (
                b'{"service":"lemonade","hostname":"workstation"}',
                "192.168.1.20",
            ),
            (
                b'{"service":"lemonade","hostname":"workstation",'
                b'"url":"file:///api/v1/"}',
                "192.168.1.20",
            ),
            (
                b'{"service":"lemonade","hostname":"workstation",'
                b'"url":"http://192.168.1.21:8000/api/v1/"}',
                "192.168.1.20",
            ),
            (
                b'{"service":"lemonade","hostname":"workstation",'
                b'"url":"http://10.0.0.20:8000/api/v1/"}',
                "10.0.0.20",
            ),
        )

        for payload, source in cases:
            with self.subTest(payload=payload, source=source):
                self.assertIsNone(
                    parse_server_beacon(
                        payload,
                        source,
                        (ip_network("192.168.1.0/24"),),
                    )
                )

    def test_enabled_adapter_networks_exclude_disabled_adapters(self) -> None:
        networks = enabled_ipv4_networks(
            [
                {
                    "enabled": True,
                    "ipv4": [
                        {"address": "192.168.1.10", "network_prefix": 24},
                        {"address": "10.0.0.5", "network_prefix": 8},
                    ],
                },
                {
                    "enabled": False,
                    "ipv4": [
                        {"address": "172.16.0.2", "network_prefix": 16},
                    ],
                },
            ]
        )

        self.assertEqual(
            (ip_network("10.0.0.0/8"), ip_network("192.168.1.0/24")),
            networks,
        )


class BeaconScannerTest(unittest.IsolatedAsyncioTestCase):
    """Specify the bounded scanner lifecycle."""

    async def test_scan_deduplicates_and_releases_the_udp_listener(self) -> None:
        transport = unittest.mock.Mock()

        async def create_endpoint(factory, **kwargs):
            protocol = factory()
            protocol.datagram_received(
                b'{"service":"lemonade","hostname":"first",'
                b'"url":"http://192.168.1.20:8000/api/v1/"}',
                ("192.168.1.20", 13305),
            )
            protocol.datagram_received(
                b'{"service":"lemonade","hostname":"duplicate",'
                b'"url":"http://192.168.1.20:8000/api/v1/"}',
                ("192.168.1.20", 13305),
            )
            return transport, protocol

        loop = asyncio.get_running_loop()
        with patch.object(
            loop,
            "create_datagram_endpoint",
            AsyncMock(side_effect=create_endpoint),
        ):
            candidates = await async_scan_server_beacons(
                (ip_network("192.168.1.0/24"),),
                duration=0,
            )

        self.assertEqual(["http://192.168.1.20:8000"], list(candidates))
        transport.close.assert_called_once_with()

    async def test_bind_failure_degrades_to_no_discovered_servers(self) -> None:
        loop = asyncio.get_running_loop()
        with patch.object(
            loop,
            "create_datagram_endpoint",
            AsyncMock(side_effect=OSError("address in use")),
        ):
            candidates = await async_scan_server_beacons((), duration=0)

        self.assertEqual({}, candidates)

    async def test_concurrent_scans_do_not_bind_the_beacon_port_together(self) -> None:
        active_listeners = 0
        maximum_active_listeners = 0

        class Transport:
            def close(self) -> None:
                nonlocal active_listeners
                active_listeners -= 1

        async def create_endpoint(factory, **kwargs):
            nonlocal active_listeners, maximum_active_listeners
            active_listeners += 1
            maximum_active_listeners = max(
                maximum_active_listeners,
                active_listeners,
            )
            return Transport(), factory()

        loop = asyncio.get_running_loop()
        with patch.object(
            loop,
            "create_datagram_endpoint",
            AsyncMock(side_effect=create_endpoint),
        ) as create:
            first, second = await asyncio.gather(
                async_scan_server_beacons((), duration=0.001),
                async_scan_server_beacons((), duration=0.001),
            )

        self.assertEqual(1, maximum_active_listeners)
        self.assertEqual(0, active_listeners)
        self.assertEqual(first, second)
        create.assert_awaited_once()
