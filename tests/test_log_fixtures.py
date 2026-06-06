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

"""End-to-end fixture tests from captured AntSDR text logs."""

from pathlib import Path

import xml.etree.ElementTree as ET

import djicot


DATA_DIR = Path(__file__).parent / "data"


def _config():
    return {
        "SENSOR_LAT": "37.76",
        "SENSOR_LON": "-122.4975",
        "SENSOR_ID": "DJICOT-TEST",
        "HIDE_INVALID_DATA": "0",
    }


def _load_fixture(name: str) -> str:
    return (DATA_DIR / name).read_text(encoding="utf-8").strip()


def _parse_cot_events(events):
    return [ET.fromstring(event.split(b"\n", maxsplit=1)[-1]) for event in events]


def test_encrypted_line_generates_range_uas_cot():
    events = djicot.handle_text_line(_load_fixture("dji_o_encrypted.txt"), _config())
    assert events
    roots = _parse_cot_events(events)
    uas = next(root for root in roots if root.attrib["uid"].endswith(".uas"))
    assert "Range" in uas.find(".//contact").attrib["callsign"]
    assert uas.find(".//__cuas").attrib["valid_geo"] == "0"
    assert uas.attrib.get("qos") == "1-r-c"


def test_full_decode_generates_uas_op_home():
    events = djicot.handle_text_line(_load_fixture("dji_o_full_decode.txt"), _config())
    roots = _parse_cot_events(events)
    uids = {root.attrib["uid"] for root in roots}
    assert "DJI.3NZCHBL003AUDW.uas" in uids
    assert "DJI.3NZCHBL003AUDW.op" in uids
    assert "DJI.3NZCHBL003AUDW.home" in uids


def test_uas_only_line_generates_uas_and_op_skips_home():
    events = djicot.handle_text_line(_load_fixture("dji_o_uas_only.txt"), _config())
    roots = _parse_cot_events(events)
    uids = {root.attrib["uid"] for root in roots}
    assert "DJI.3NZCHBL003AUDW.uas" in uids
    assert "DJI.3NZCHBL003AUDW.op" not in uids
    assert "DJI.3NZCHBL003AUDW.home" not in uids
    uas = next(root for root in roots if root.attrib["uid"].endswith(".uas"))
    assert uas.find(".//__dh-uas") is not None
