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

"""DJICOT Constants."""

# IP address of ANT SDR E200 running DJI Drone ID firmware:
DEFAULT_FEED_URL: str = "tcp://192.168.1.10:41030"
DEFAULT_TEXT_FEED_URL: str = "tcp://192.168.1.10:52002"
DEFAULT_BINARY_PORT: int = 41030
DEFAULT_TEXT_PORT: int = 52002
DEFAULT_COT_TYPE: str = "a-u-A-M-H-Q"

DEFAULT_SENSOR_LAT: str = "0.0"
DEFAULT_SENSOR_LON: str = "0.0"

DEFAULT_SENSOR_ID: str = "DJICOT"
DEFAULT_SENSOR_NAME: str = "DJICOT"
DEFAULT_SENSOR_DETAIL: str = "DJICOT is a DJI Drone ID to TAK Gateway"
DEFAULT_SENSOR_TYPE: str = "DJIDroneID"
DEFAULT_SENSOR_UID: str = "DJICOT-0001"
DEFAULT_SENSOR_CONTACT: str = "info@snstac.com"
DEFAULT_SENSOR_COT_TYPE: str = "a-f-G-E-S-E"
DEFAULT_SENSOR_STALE: str = "600"
DEFAULT_SENSOR_SN: str = "0001"
DEFAULT_SENSOR_HAE: str = "9999999.0"
DEFAULT_SENSOR_CE: str = "9999999.0"
DEFAULT_SENSOR_LE: str = "9999999.0"

DEFAULT_READ_BYTES: int = 1024
DEFAULT_BREAD_CRUMBS_ENABLED: int = 1
DEFAULT_HIDE_INVALID_DATA: int = 0
