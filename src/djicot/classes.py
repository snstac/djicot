#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""DJICOT Class Definitions."""

import asyncio
import time
from configparser import SectionProxy
from pathlib import Path
from typing import Optional, Union
from urllib.parse import ParseResult, urlparse

from pytak import QueueWorker

from djicot import (
    DEFAULT_FEED_URL,
    DEFAULT_READ_BYTES,
    handle_frame,
    handle_text_line,
    xml_to_cot,
)


def _config_bool(config: Union[SectionProxy, dict], key: str, default: bool = False) -> bool:
    if not config:
        return default
    if hasattr(config, "getboolean"):
        try:
            return config.getboolean(key, fallback=default)
        except ValueError:
            return default
    val = config.get(key, default)
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("1", "true", "yes", "on")


class DJIWorker(QueueWorker):
    """Process DJI Drone ID data from the net queue and emit CoT events."""

    def __init__(
        self,
        tx_queue: asyncio.Queue,
        config: Union[SectionProxy, dict],
        net_queue: asyncio.Queue,
    ) -> None:
        super().__init__(tx_queue, config)
        self.net_queue = net_queue

    async def handle_data(self, data) -> None:
        """Convert raw feed data to CoT and enqueue for transmission."""
        self._logger.debug("Received data: %s", data)
        if isinstance(data, str):
            events = handle_text_line(data, self.config)
        elif isinstance(data, bytes) and data.startswith(b"dji_O,"):
            events = handle_text_line(data.decode("utf-8", errors="replace"), self.config)
        else:
            events = handle_frame(data, self.config)
        for event in events:
            await self.put_queue(event)

    async def hello_event(self, init: bool = False) -> None:
        """Send periodic sensor hello CoT unless PYTAK_NO_HELLO is set."""
        if _config_bool(self.config, "PYTAK_NO_HELLO"):
            return
        if init or int(time.time()) % 60 == 0:
            event: Optional[bytes] = xml_to_cot(
                f"init={init}", self.config, "sensor_to_cot"
            )
            await self.put_queue(event)

    async def run(self, _=-1) -> None:
        self._logger.info("Running %s", self.__class__)

        if not _config_bool(self.config, "PYTAK_NO_HELLO"):
            await self.hello_event(init=True)

        while True:
            if not _config_bool(self.config, "PYTAK_NO_HELLO"):
                await self.hello_event()
            received = await self.net_queue.get()
            if not received:
                continue
            await self.handle_data(received)


class _FeedWorker(QueueWorker):
    """Base class for feed workers that enqueue raw data."""

    async def handle_data(self, data) -> None:
        self.queue.put_nowait(data)


class BinaryNetWorker(_FeedWorker):
    """Read binary DJI Drone ID frames from a TCP connection (port 41030)."""

    async def run(self, _=-1) -> None:
        url: ParseResult = urlparse(self.config.get("FEED_URL", DEFAULT_FEED_URL))
        self._logger.info("Running %s for %s", self.__class__, url.geturl())

        host, port = url.netloc.split(":")
        reader, _ = await asyncio.open_connection(host, int(port))

        read_bytes = int(self.config.get("READ_BYTES", DEFAULT_READ_BYTES))
        while True:
            received = await reader.read(read_bytes)
            if received:
                await self.handle_data(received)


class TextNetWorker(_FeedWorker):
    """Read AntSDR text CSV lines from a TCP connection (port 52002)."""

    async def run(self, _=-1) -> None:
        url: ParseResult = urlparse(self.config.get("FEED_URL", DEFAULT_FEED_URL))
        self._logger.info("Running %s for %s", self.__class__, url.geturl())

        host, port = url.netloc.split(":")
        reader, _ = await asyncio.open_connection(host, int(port))

        buffer = b""
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                continue
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", maxsplit=1)
                text = line.decode("utf-8", errors="replace").strip()
                if text.startswith("dji_O,"):
                    await self.handle_data(text)


class FileReplayWorker(_FeedWorker):
    """Replay AntSDR text log lines from a local file for offline evaluation."""

    async def run(self, _=-1) -> None:
        url: ParseResult = urlparse(self.config.get("FEED_URL", DEFAULT_FEED_URL))
        path = Path(url.path)
        self._logger.info("Running %s for %s", self.__class__, path)

        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                text = line.strip()
                if text.startswith("dji_O,"):
                    await self.handle_data(text)
                await asyncio.sleep(0)


# Backward-compatible alias for the original binary TCP worker.
NetWorker = BinaryNetWorker
