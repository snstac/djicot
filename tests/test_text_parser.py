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

"""Text parser tests for AntSDR dji_O CSV lines."""

from pathlib import Path

import djicot.text_parser as text_parser


DATA_DIR = Path(__file__).parent / "data"


def _load_fixture(name: str) -> str:
    return (DATA_DIR / name).read_text(encoding="utf-8").strip()


def test_parse_encrypted_line():
    parsed = text_parser.parse_text_line(_load_fixture("dji_o_encrypted.txt"))
    assert parsed is not None
    assert parsed["device_type"] == "dji(4aced727)"
    assert parsed["serial_number"] is None
    assert parsed["device_type_8"] == 4
    assert parsed["rssi"] == -110
    assert parsed["freq"] == 5776.5


def test_parse_full_decode_line():
    parsed = text_parser.parse_text_line(_load_fixture("dji_o_full_decode.txt"))
    assert parsed is not None
    assert parsed["serial_number"] == "3NZCHBL003AUDW"
    assert parsed["device_type"].startswith("DJI Mini 2")
    assert parsed["op_lon"] == -122.497339
    assert parsed["op_lat"] == 37.76
    assert parsed["home_lon"] == -122.497327
    assert parsed["home_lat"] == 37.760005
    assert parsed["speed_e"] == 6.5
    assert parsed["speed_n"] == 0.0


def test_parse_uas_only_line():
    parsed = text_parser.parse_text_line(_load_fixture("dji_o_uas_only.txt"))
    assert parsed is not None
    assert parsed["uas_lon"] == -122.497677
    assert parsed["uas_lat"] == 37.760034
    assert parsed["op_lat"] == 0.0
    assert parsed["home_lat"] == 0.0


def test_parse_invalid_line():
    assert text_parser.parse_text_line("") is None
    assert text_parser.parse_text_line("not,a,valid,line") is None
