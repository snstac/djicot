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

"""
DJI Drone ID to TAK Gateway.

This module serves as the entry point for the DJI to TAK Gateway application.
It imports and exposes constants, functions, and classes necessary for the
operation of the gateway.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("djicot")
except PackageNotFoundError:
    from pathlib import Path

    __version__ = Path(__file__).resolve().parent.joinpath("VERSION").read_text(encoding="utf-8").strip()

from .constants import (  # NOQA
    DEFAULT_FEED_URL,
    DEFAULT_TEXT_FEED_URL,
    DEFAULT_BINARY_PORT,
    DEFAULT_TEXT_PORT,
    DEFAULT_COT_TYPE,
    DEFAULT_SENSOR_LAT,
    DEFAULT_SENSOR_LON,
    DEFAULT_SENSOR_HAE,
    DEFAULT_SENSOR_LE,
    DEFAULT_SENSOR_CE,
    DEFAULT_SENSOR_ID,
    DEFAULT_SENSOR_NAME,
    DEFAULT_SENSOR_DETAIL,
    DEFAULT_SENSOR_STALE,
    DEFAULT_SENSOR_TYPE,
    DEFAULT_SENSOR_UID,
    DEFAULT_SENSOR_CONTACT,
    DEFAULT_SENSOR_COT_TYPE,
    DEFAULT_SENSOR_SN,
    DEFAULT_READ_BYTES,
    DEFAULT_BREAD_CRUMBS_ENABLED,
    DEFAULT_HIDE_INVALID_DATA,
)

from .functions import (  # NOQA
    create_tasks,
    xml_to_cot,
    handle_frame,
    handle_text_line,
    handle_parsed_data,
)

from .classes import (  # NOQA
    DJIWorker,
    BinaryNetWorker,
    TextNetWorker,
    FileReplayWorker,
    NetWorker,
)

from .text_parser import parse_text_line  # NOQA
