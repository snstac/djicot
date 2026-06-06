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

"""DJICOT Functions."""

import asyncio
import logging
import os
import xml.etree.ElementTree as ET

from configparser import SectionProxy
from typing import Optional, Set, Union
from urllib.parse import urlparse

import pytak
import djicot

from .dji_functions import parse_frame, parse_data
from .text_parser import parse_text_line


APP_NAME = "djicot"
Logger = logging.getLogger(__name__)
Debug = bool(os.getenv("DEBUG", False))
if Debug:
    Logger.setLevel(logging.DEBUG)


def _config_bool(config: Union[SectionProxy, dict, None], key: str, default: bool = False) -> bool:
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


def _feed_uses_text(config: SectionProxy) -> bool:
    feed_format = str(config.get("FEED_FORMAT", "")).lower()
    if feed_format == "text":
        return True
    feed_url = str(config.get("FEED_URL", djicot.DEFAULT_FEED_URL)).lower()
    if feed_url.startswith("file://"):
        return True
    parsed = urlparse(feed_url)
    if parsed.scheme == "file":
        return True
    if parsed.port == djicot.DEFAULT_TEXT_PORT:
        return True
    return False


def create_tasks(config: SectionProxy, clitool: pytak.CLITool) -> Set[pytak.Worker,]:
    """Create specific coroutine task set for this application."""
    tasks = set()
    net_queue: asyncio.Queue = asyncio.Queue()

    if _feed_uses_text(config):
        feed_url = str(config.get("FEED_URL", djicot.DEFAULT_FEED_URL)).lower()
        if feed_url.startswith("file://") or urlparse(feed_url).scheme == "file":
            tasks.add(djicot.FileReplayWorker(net_queue, config))
        else:
            tasks.add(djicot.TextNetWorker(net_queue, config))
    else:
        tasks.add(djicot.BinaryNetWorker(net_queue, config))

    tasks.add(djicot.DJIWorker(clitool.tx_queue, config, net_queue))
    return tasks


def dji_uas_to_cot(
    data, config: Union[SectionProxy, dict, None] = None
) -> Optional[ET.Element]:
    """Convert DJI UAS data to CoT."""
    return gen_dji_cot(data, config, "uas")


def dji_op_to_cot(
    data, config: Union[SectionProxy, dict, None] = None
) -> Optional[ET.Element]:
    """Convert DJI Operator data to CoT."""
    return gen_dji_cot(data, config, "op")


def dji_home_to_cot(
    data, config: Union[SectionProxy, dict, None] = None
) -> Optional[ET.Element]:
    """Convert DJI Home data to CoT"""
    return gen_dji_cot(data, config, "home")


def is_valid_lat_lon(lat, lon) -> bool:
    """Validate latitude and longitude values."""
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        if lat_f == 0.0 or lon_f == 0.0:
            return False
        return -90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0
    except (TypeError, ValueError):
        return False


def _append_dh_uas(detail: ET.Element, data: dict, config: dict, uas_sn: str) -> None:
    sensor_id = str(config.get("SENSOR_ID", djicot.DEFAULT_SENSOR_ID))
    dh_uas = ET.Element("__dh-uas")

    metadata = ET.Element("metadata")
    metadata.set("serialNumber", str(uas_sn))
    metadata.set("description", str(data.get("device_type", "")))
    dh_uas.append(metadata)

    connection_data = ET.Element("connectionData")
    connection_data.set("receivedBy", sensor_id)
    connection_data.set("rssi", str(data.get("rssi", "")))
    connection_data.set("receiverSrc", str(config.get("SENSOR_TYPE", djicot.DEFAULT_SENSOR_TYPE)))
    dh_uas.append(connection_data)

    kinematic_data = ET.Element("kinematicData")
    kinematic_data.set("horizontalSpeed", str(data.get("speed_e", "")))
    kinematic_data.set("verticalSpeed", str(data.get("speed_u", "")))
    dh_uas.append(kinematic_data)

    detail.append(dh_uas)


def gen_dji_cot(  # NOQA pylint: disable=too-many-locals,too-many-branches,too-many-statements
    data, config: Union[SectionProxy, dict, None] = None, leg="uas"
) -> Optional[ET.Element]:
    """Generate a Cursor on Target (CoT) XML Event from DJI data."""
    config = config or {}

    lat = data.get(f"{leg}_lat")
    lon = data.get(f"{leg}_lon")

    lat_lon_valid = is_valid_lat_lon(lat, lon)
    if not lat_lon_valid:
        lat = None
        lon = None
    Logger.debug("leg=%s lat=%s lon=%s", leg, lat, lon)

    hide_invalid = _config_bool(
        config, "HIDE_INVALID_DATA", bool(djicot.DEFAULT_HIDE_INVALID_DATA)
    )
    if not lat_lon_valid and hide_invalid:
        Logger.debug("Hiding invalid %s data", leg)
        return None

    freq = str(data.get("freq", 0.0))
    rssi = str(data.get("rssi", -999))
    serial_number = data.get("serial_number")
    uas_sn = serial_number or freq
    uas_type = data.get("device_type", "")

    cot_type: str = str(config.get("COT_TYPE", djicot.DEFAULT_COT_TYPE))
    if leg == "op" or leg == "home":
        cot_type = str("a-u-G-U-C")

    cot_uid = f"DJI.{uas_sn}.{leg}"
    callsign = f"{uas_sn}.{leg}"
    ce = str(data.get("nac_p", pytak.DEFAULT_COT_VAL))

    if not lat_lon_valid:
        if leg == "op" or leg == "home":
            Logger.debug("No %s lat/lon", leg)
            return None
        if leg == "uas":
            lat = config.get("SENSOR_LAT", djicot.DEFAULT_SENSOR_LAT)
            lon = config.get("SENSOR_LON", djicot.DEFAULT_SENSOR_LON)
            cot_type = str("a-u-A-M-H-Q")
            callsign = f"{callsign} (Range)"
            ce = str(1000.0 * abs(int(float(rssi))))
            Logger.debug("No UAS lat/lon, using sensor lat/lon: %s, %s", lat, lon)

    remarks_fields: list = []

    cot_stale: int = int(config.get("COT_STALE", pytak.DEFAULT_COT_STALE))
    cot_host_id: str = config.get("COT_HOST_ID", pytak.DEFAULT_HOST_ID)
    sensor_id = str(config.get("SENSOR_ID", djicot.DEFAULT_SENSOR_ID))

    cuas = ET.Element("__cuas")
    cuas.set("sensor_id", sensor_id)
    cuas.set("sensor_sn", str(config.get("SENSOR_SN", djicot.DEFAULT_SENSOR_SN)))
    cuas.set("sensor_type", str(config.get("SENSOR_TYPE", djicot.DEFAULT_SENSOR_TYPE)))
    cuas.set("sensor_name", str(config.get("SENSOR_NAME", djicot.DEFAULT_SENSOR_NAME)))
    cuas.set("cot_host_id", cot_host_id)
    cuas.set("uas_type", uas_type)
    cuas.set("uas_type_8", str(data.get("device_type_8")))
    cuas.set("uas_sn", str(uas_sn))
    cuas.set("freq", freq)
    cuas.set("rssi", rssi)
    cuas.set("speed_e", str(data.get("speed_e", 0.0)))
    cuas.set("speed_n", str(data.get("speed_n", 0.0)))
    cuas.set("speed_u", str(data.get("speed_u", 0.0)))
    if lat_lon_valid:
        cuas.set("valid_geo", "1")
        cuas.set("sn_present", "1")
        cuas.set("serial_valid", "1")
    else:
        cuas.set("valid_geo", "0")
        cuas.set("sn_present", "0")
        cuas.set("serial_valid", "0")

    crumbs = ET.Element("__bread_crumbs")
    crumbs.set(
        "enabled",
        str(config.get("BREAD_CRUMBS_ENABLED", djicot.DEFAULT_BREAD_CRUMBS_ENABLED)),
    )

    contact: ET.Element = ET.Element("contact")
    contact.set("callsign", callsign)

    track: ET.Element = ET.Element("track")
    track.set("course", data.get("course_point", pytak.DEFAULT_COT_VAL))
    track.set("speed", data.get("speed_point", pytak.DEFAULT_COT_VAL))

    detail = ET.Element("detail")

    remarks = ET.Element("remarks")
    remarks_fields.append(f"sn={uas_sn}")
    remarks_fields.append(f"({uas_type})")
    remarks_fields.append(f"freq={data.get('freq', 0.0)}")
    remarks_fields.append(f"rss={data.get('rssi', 0)}")
    remarks_fields.append(f"speed={data.get('speed_e', 0.0)}")
    remarks_fields.append(f"sensor_id={sensor_id}")
    remarks_fields.append(f"host_id={cot_host_id}")
    remarks.text = " ".join(filter(None, remarks_fields))
    detail.append(remarks)

    detail.append(contact)
    detail.append(track)
    detail.append(cuas)
    detail.append(crumbs)

    if leg == "uas":
        op_uid = f"DJI.{uas_sn}.op"
        link = ET.Element("link")
        link.set("uid", op_uid)
        link.set("type", "a-u-G-U-C")
        link.set("parent_callsign", callsign)
        link.set("relation", "p-p")
        detail.append(link)

        creator = ET.Element("creator")
        creator.set("uid", op_uid)
        creator.set("callsign", callsign)
        creator.set("type", "a-u-G-U-C")
        detail.append(creator)
        _append_dh_uas(detail, data, config, str(uas_sn))

    le = str(data.get("nac_v", pytak.DEFAULT_COT_VAL))
    hae = str(data.get("alt_geom", pytak.DEFAULT_COT_VAL))

    cot_d = {
        "lat": str(lat),
        "lon": str(lon),
        "ce": ce,
        "le": le,
        "hae": hae,
        "uid": cot_uid,
        "cot_type": cot_type,
        "stale": cot_stale,
    }
    cot = pytak.gen_cot_xml(**cot_d)
    cot.set("access", config.get("COT_ACCESS", pytak.DEFAULT_COT_ACCESS))
    cot.set("qos", "1-r-c")

    _detail = cot.find("detail")
    if _detail is not None:
        flowtags = _detail.findall("_flow-tags_")
        detail.extend(flowtags)
        cot.remove(_detail)
    cot.append(detail)

    return cot


def sensor_to_cot(
    data, config: Union[SectionProxy, dict, None] = None
) -> Optional[ET.Element]:
    """Create a CoT Event for the Sensor."""
    config = config or {}

    lat = config.get("SENSOR_LAT", djicot.DEFAULT_SENSOR_LAT)
    lon = config.get("SENSOR_LON", djicot.DEFAULT_SENSOR_LON)

    if lat is None or lon is None:
        Logger.debug("No Sensor Lat/Lon")
        return None

    sensor_id = config.get("SENSOR_ID", djicot.DEFAULT_SENSOR_ID)
    sensor_sn = config.get("SENSOR_SN", djicot.DEFAULT_SENSOR_SN)
    sensor_type = config.get("SENSOR_TYPE", djicot.DEFAULT_SENSOR_TYPE)

    cot_host_id: str = config.get("COT_HOST_ID", pytak.DEFAULT_HOST_ID)

    cot_uid = config.get("SENSOR_UID", f"CUAS-{sensor_type}-{sensor_sn}-{cot_host_id}")
    callsign = config.get("SENSOR_CALLSIGN", f"CUAS-{sensor_type}-{sensor_sn}")

    cot_type = config.get("SENSOR_COT_TYPE", djicot.DEFAULT_SENSOR_COT_TYPE)
    cot_stale = config.get("SENSOR_STALE", djicot.DEFAULT_SENSOR_STALE)

    cuas = ET.Element("__cuas")
    cuas.set("sensor_id", sensor_id)
    cuas.set("sensor_sn", sensor_sn)
    cuas.set("sensor_type", sensor_type)
    cuas.set("cot_host_id", cot_host_id)

    contact: ET.Element = ET.Element("contact")
    contact.set("callsign", callsign)

    detail = ET.Element("detail")

    remarks = ET.Element("remarks")
    remarks.text = (
        f"sensor_id={sensor_id} sensor_sn={sensor_sn} "
        f"sensor_type={sensor_type} cot_host_id={cot_host_id}: {data}"
    )

    detail.append(remarks)
    detail.append(contact)
    detail.append(cuas)

    cot_d = {
        "lat": str(lat),
        "lon": str(lon),
        "ce": str(config.get("SENSOR_CE", djicot.DEFAULT_SENSOR_CE)),
        "le": str(config.get("SENSOR_LE", djicot.DEFAULT_SENSOR_LE)),
        "hae": str(config.get("SENSOR_HAE", djicot.DEFAULT_SENSOR_HAE)),
        "uid": cot_uid,
        "cot_type": cot_type,
        "stale": cot_stale,
    }
    cot = pytak.gen_cot_xml(**cot_d)
    cot.set("access", config.get("COT_ACCESS", pytak.DEFAULT_COT_ACCESS))
    cot.set("qos", "1-r-c")

    _detail = cot.find("detail")
    if _detail is not None:
        flowtags = _detail.findall("_flow-tags_")
        detail.extend(flowtags)
        cot.remove(_detail)
    cot.append(detail)

    return cot


def xml_to_cot(
    data: dict, config: Union[SectionProxy, dict, None] = None, func: Optional[str] = None
) -> Optional[bytes]:
    """Convert data to a CoT XML string using the specified function."""
    cot: Optional[ET.Element] = getattr(djicot.functions, func)(data, config)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)])
        if cot is not None
        else None
    )


def handle_parsed_data(
    parsed_data: dict, config: Union[SectionProxy, dict, None] = None
) -> list:
    """Generate CoT events from parsed DJI data."""
    config = config or {}
    events = []
    funcs = ["dji_uas_to_cot", "dji_op_to_cot", "dji_home_to_cot"]
    for func in funcs:
        event: Optional[bytes] = xml_to_cot(parsed_data, config, func)
        if event:
            events.append(event)
    return events


def handle_text_line(
    line: str, config: Union[SectionProxy, dict, None] = None
) -> list:
    """Parse an AntSDR text CSV line and return CoT event bytes."""
    config = config or {}
    parsed_data = parse_text_line(line)
    if not parsed_data:
        return []
    Logger.debug("Parsed DJI text line: %s", parsed_data)
    return handle_parsed_data(parsed_data, config)


def handle_frame(
    frame: bytearray, config: Union[SectionProxy, dict, None] = None
) -> list:
    """Parse a binary DJI Drone ID frame and return CoT event bytes."""
    config = config or {}

    try:
        package_type, data = parse_frame(frame)
    except Exception as exc:
        Logger.warning("Error parsing DJI frame: %s", exc)
        return []

    if package_type != 0x01:
        Logger.warning("Invalid DJI package type: %s", package_type)

    if not data:
        Logger.warning("No DJI data")
        return []

    try:
        parsed_data = parse_data(data)
    except Exception as exc:
        Logger.warning("Error parsing DJI data: %s", exc)
        parsed_data = {}

    Logger.debug("Parsed DJI data: %s", parsed_data)
    return handle_parsed_data(parsed_data, config)
