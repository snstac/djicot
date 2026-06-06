#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Optional live AntSDR integration tests."""

import asyncio
import ipaddress
import os
import socket
from typing import Optional

import pytest

import djicot


DEFAULT_HOST = "192.168.1.10"
BINARY_PORT = djicot.DEFAULT_BINARY_PORT
TEXT_PORT = djicot.DEFAULT_TEXT_PORT
DISCOVERY_SUBNET = os.getenv("ANTSDR_SUBNET", "172.26.30.0/24")


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _discover_antsdr_host() -> Optional[str]:
    env_host = os.getenv("ANTSDR_HOST")
    if env_host and (_port_open(env_host, BINARY_PORT) or _port_open(env_host, TEXT_PORT)):
        return env_host

    try:
        network = ipaddress.ip_network(DISCOVERY_SUBNET, strict=False)
    except ValueError:
        return None

    for host in network.hosts():
        host_str = str(host)
        if _port_open(host_str, BINARY_PORT) or _port_open(host_str, TEXT_PORT):
            return host_str
    return None


@pytest.fixture(scope="module")
def antsdr_host():
    host = _discover_antsdr_host()
    if not host:
        pytest.skip("No AntSDR found; set ANTSDR_HOST or connect to ANTSDR_SUBNET")
    return host


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_binary_feed_smoke(antsdr_host):
    if not _port_open(antsdr_host, BINARY_PORT):
        pytest.skip(f"Binary port {BINARY_PORT} not open on {antsdr_host}")

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(antsdr_host, BINARY_PORT), timeout=5
    )
    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=10)
    finally:
        writer.close()
        await writer.wait_closed()

    assert data
    if data.startswith(b"dji_O,"):
        events = djicot.handle_text_line(data.decode("utf-8", errors="replace"))
    else:
        events = djicot.handle_frame(data)
    if os.getenv("DJICOT_LIVE_COT") == "1":
        assert events is not None


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_text_feed_smoke(antsdr_host):
    if not _port_open(antsdr_host, TEXT_PORT):
        pytest.skip(f"Text port {TEXT_PORT} not open on {antsdr_host}")

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(antsdr_host, TEXT_PORT), timeout=5
    )
    try:
        buffer = b""
        parsed_line = None
        for _ in range(20):
            chunk = await asyncio.wait_for(reader.read(4096), timeout=10)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", maxsplit=1)
                text = line.decode("utf-8", errors="replace").strip()
                if text.startswith("dji_O,"):
                    parsed_line = text
                    break
            if parsed_line:
                break
    finally:
        writer.close()
        await writer.wait_closed()

    assert parsed_line is not None
    parsed = djicot.parse_text_line(parsed_line)
    assert parsed is not None
    if os.getenv("DJICOT_LIVE_COT") == "1":
        events = djicot.handle_text_line(parsed_line, {"SENSOR_LAT": "0", "SENSOR_LON": "0"})
        assert events is not None
