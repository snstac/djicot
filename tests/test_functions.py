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

"""DJICOT Function Tests."""

import struct
import unittest

import xml.etree.ElementTree as ET

import djicot
import djicot.dji_functions


class FunctionsTestCase(unittest.TestCase):
    """
    Test class for functions... functions.
    """

    def test_parse_data(self):
        """Test parse_data function with valid data."""

        data = bytearray(227)
        data[:64] = b"serial_number".ljust(64, b"\x00")
        data[64:128] = b"device_type".ljust(64, b"\x00")
        data[128] = 8
        data[129:137] = struct.pack("d", 37.7749)  # app_lat
        data[137:145] = struct.pack("d", -122.4194)  # app_lon
        data[145:153] = struct.pack("d", 37.7749)  # uas_lat
        data[153:161] = struct.pack("d", -122.4194)  # uas_lon
        data[161:169] = struct.pack("d", 100.0)  # height
        data[169:177] = struct.pack("d", 200.0)  # altitude
        data[177:185] = struct.pack("d", 37.7749)  # home_lat
        data[185:193] = struct.pack("d", -122.4194)  # home_lon
        data[193:201] = struct.pack("d", 2.4)  # freq
        data[201:209] = struct.pack("d", 10.0)  # speed_e
        data[209:217] = struct.pack("d", 5.0)  # speed_n
        data[217:225] = struct.pack("d", 1.0)  # speed_u
        data[225:227] = struct.pack("h", -50)  # rssi

        parsed_data = djicot.dji_functions.parse_data(data)
        print("parsed_data")
        print(parsed_data)
        assert parsed_data.get("serial_number") == "serial_number"
        assert parsed_data.get("device_type") == "device_type"
        assert parsed_data.get("device_type_8") == 8
        assert parsed_data.get("op_lat") == 37.7749
        assert parsed_data.get("op_lon") == -122.4194
        assert parsed_data.get("uas_lat") == 37.7749
        assert parsed_data.get("uas_lon") == -122.4194
        assert parsed_data.get("height") == 100.0
        assert parsed_data.get("altitude") == 200.0
        assert parsed_data.get("home_lat") == 37.7749
        assert parsed_data.get("home_lon") == -122.4194
        assert parsed_data.get("freq") == 2.4
        assert parsed_data.get("speed_e") == 10.0
        assert parsed_data.get("speed_n") == 5.0
        assert parsed_data.get("speed_u") == 1.0
        assert parsed_data.get("rssi") == -50

    def _test_parse_data_with_invalid_data(self):
        """Test parse_data function with invalid data."""
        data = b"invalid_data"
        parsed_data = djicot.dji_functions.parse_data(data)
        assert parsed_data["device_type"] == "Got a DJI drone with encryption"
        assert parsed_data["device_type_8"] == 255

    def test_parse_frame(self):
        """Test parse_frame function with valid frame data."""
        frame = bytearray(10)
        frame[:2] = b"\x01\x02"  # frame_header
        frame[2] = 0x03  # package_type
        frame[3:5] = struct.pack("H", 10)  # package_length
        frame[5:10] = b"hello"  # data

        package_type, data = djicot.functions.parse_frame(frame)
        assert package_type == 0x03
        assert data == b"hello"

    def test_parse_frame_with_invalid_length(self):
        """Test parse_frame function with invalid length."""
        frame = bytearray(8)
        frame[:2] = b"\x01\x02"  # frame_header
        frame[2] = 0x03  # package_type
        frame[3:5] = struct.pack("H", 10)  # package_length
        frame[5:8] = b"hel"  # data

        package_type, data = djicot.functions.parse_frame(frame)
        assert package_type == 0x03
        assert data == b"hel"

    def test_handle_frame_valid(self):
        """Test handle_frame function with valid frame data."""
        frame = bytearray(10)
        frame[:2] = b"\x01\x02"  # frame_header
        frame[2] = 0x01  # package_type

        data = bytearray(227)
        data[:64] = b"F4XF7249QM06Q26P".ljust(64, b"\x00")
        data[64:128] = b"DJI Mini 3 pro".ljust(64, b"\x00")
        data[128] = 73
        data[129:137] = struct.pack("d", 37.7749)  # app_lat
        data[137:145] = struct.pack("d", -122.4194)  # app_lon
        data[145:153] = struct.pack("d", 37.7749)  # uas_lat
        data[153:161] = struct.pack("d", -122.4194)  # uas_lon
        data[161:169] = struct.pack("d", 100.0)  # height
        data[169:177] = struct.pack("d", 200.0)  # altitude
        data[177:185] = struct.pack("d", 37.7749)  # home_lat
        data[185:193] = struct.pack("d", -122.4194)  # home_lon
        data[193:201] = struct.pack("d", 2.4)  # freq
        data[201:209] = struct.pack("d", 10.0)  # speed_e
        data[209:217] = struct.pack("d", 5.0)  # speed_n
        data[217:225] = struct.pack("d", 1.0)  # speed_u
        data[225:227] = struct.pack("h", -50)  # rssi

        frame[3:5] = struct.pack("H", len(data) + 5)  # package_length includes header
        frame[5 : 5 + len(data)] = data

        config = {
            "DEBUG": True,
            "COT_TYPE": "a-f-G-U-C",
            "COT_STALE": 600,
            "COT_HOST_ID": "test_host",
            "SENSOR_ID": "test_sensor",
            "SENSOR_SN": "test_sn",
            "SENSOR_TYPE": "test_type",
            "SENSOR_NAME": "test_name",
            "COT_ACCESS": "test_access",
        }

        events = djicot.functions.handle_frame(frame, config)
        assert len(events) == 3
        for event in events:
            assert b"F4XF7249QM06Q26P" in event

    def test_handle_frame_invalid_package_type(self):
        """Test handle_frame function with invalid package type."""
        frame = bytearray(10)
        frame[:2] = b"\x01\x02"  # frame_header
        frame[2] = 0x02  # invalid package_type

        data = bytearray(227)
        data[:64] = b"F4XF7249QM06Q26P".ljust(64, b"\x00")
        data[64:128] = b"DJI Mini 3 pro".ljust(64, b"\x00")
        data[128] = 73
        data[129:137] = struct.pack("d", 37.7749)  # app_lat
        data[137:145] = struct.pack("d", -122.4194)  # app_lon
        data[145:153] = struct.pack("d", 37.7749)  # uas_lat
        data[153:161] = struct.pack("d", -122.4194)  # uas_lon
        data[161:169] = struct.pack("d", 100.0)  # height
        data[169:177] = struct.pack("d", 200.0)  # altitude
        data[177:185] = struct.pack("d", 37.7749)  # home_lat
        data[185:193] = struct.pack("d", -122.4194)  # home_lon
        data[193:201] = struct.pack("d", 2.4)  # freq
        data[201:209] = struct.pack("d", 10.0)  # speed_e
        data[209:217] = struct.pack("d", 5.0)  # speed_n
        data[217:225] = struct.pack("d", 1.0)  # speed_u
        data[225:227] = struct.pack("h", -50)  # rssi

        frame[3:5] = struct.pack("H", len(data) + 5)  # package_length includes header
        frame[5 : 5 + len(data)] = data

        config = {
            "DEBUG": True,
            "COT_TYPE": "a-f-G-U-C",
            "COT_STALE": 600,
            "COT_HOST_ID": "test_host",
            "SENSOR_ID": "test_sensor",
            "SENSOR_SN": "test_sn",
            "SENSOR_TYPE": "test_type",
            "SENSOR_NAME": "test_name",
            "COT_ACCESS": "test_access",
        }

        events = djicot.functions.handle_frame(frame, config)
        assert len(events) == 3
        for event in events:
            assert b"F4XF7249QM06Q26P" in event

    def test_handle_frame_invalid_data(self):
        """Test handle_frame function with invalid data."""
        frame = bytearray(10)
        frame[:2] = b"\x01\x02"  # frame_header
        frame[2] = 0x01  # package_type
        frame[3:5] = struct.pack("H", 10)  # package_length
        frame[5:10] = b"hello"  # invalid data

        config = {
            "DEBUG": True,
            "COT_TYPE": "a-f-G-U-C",
            "COT_STALE": 600,
            "COT_HOST_ID": "test_host",
            "SENSOR_ID": "test_sensor",
            "SENSOR_SN": "test_sn",
            "SENSOR_TYPE": "test_type",
            "SENSOR_NAME": "test_name",
            "COT_ACCESS": "test_access",
        }

        events = djicot.functions.handle_frame(frame, config)
        assert len(events) == 1
        for event in events:
            assert "sensor_id" in event.decode("utf-8")

    def _test_dji_to_cot(self):
        """Test dji_to_cot function with valid data."""
        frame = bytearray(10)
        frame[:2] = b"\x01\x02"  # frame_header
        frame[2] = 0x01  # package_type

        data = bytearray(227)
        data[:64] = b"F4XF7249QM06Q26P".ljust(64, b"\x00")
        data[64:128] = b"DJI Mini 3 pro".ljust(64, b"\x00")
        data[128] = 73
        data[129:137] = struct.pack("d", 37.7749)  # app_lat
        data[137:145] = struct.pack("d", -122.4194)  # app_lon
        data[145:153] = struct.pack("d", 37.7749)  # uas_lat
        data[153:161] = struct.pack("d", -122.4194)  # uas_lon
        data[161:169] = struct.pack("d", 100.0)  # height
        data[169:177] = struct.pack("d", 200.0)  # altitude
        data[177:185] = struct.pack("d", 37.7749)  # home_lat
        data[185:193] = struct.pack("d", -122.4194)  # home_lon
        data[193:201] = struct.pack("d", 2.4)  # freq
        data[201:209] = struct.pack("d", 10.0)  # speed_e
        data[209:217] = struct.pack("d", 5.0)  # speed_n
        data[217:225] = struct.pack("d", 100.0)  # speed_u
        data[225:227] = struct.pack("h", -50)  # rssi

        frame[3:5] = struct.pack("H", len(data) + 5)  # package_length includes header
        frame[5 : 5 + len(data)] = data
        print(frame)
        config = {
            "DEBUG": True,
            "COT_TYPE": "a-f-G-U-C",
            "COT_STALE": 600,
            "COT_HOST_ID": "test_host",
            "SENSOR_ID": "test_sensor",
            "SENSOR_SN": "test_sn",
            "SENSOR_TYPE": "test_type",
            "SENSOR_NAME": "test_name",
            "COT_ACCESS": "test_access",
        }

        cot = djicot.functions.dji_uas_to_cot(frame, config)
        print(ET.tostring(cot))
        assert cot is not None
        assert cot.find("detail/__cuas").get("sensor_id") == "test_sensor"
        assert cot.find("detail/__cuas").get("uas_sn") == "serial_number"
        assert cot.find("detail/__cuas").get("uas_type") == "device_type"
        assert cot.find("detail/__cuas").get("freq") == "2.4"
        assert cot.find("detail/__cuas").get("rssi") == "-50"

    def _test_dji_to_cot_invalid_package_type(self):
        """Test dji_to_cot function with invalid package type."""
        data = bytearray(227)
        data[:2] = b"\x01\x00"  # frame_header
        data[2] = 0x02  # invalid package_type
        data[3:5] = struct.pack("H", 227)  # package_length

        config = {
            "DEBUG": True,
            "COT_TYPE": "a-f-G-U-C",
            "COT_STALE": 600,
            "COT_HOST_ID": "test_host",
            "SENSOR_ID": "test_sensor",
            "SENSOR_SN": "test_sn",
            "SENSOR_TYPE": "test_type",
            "SENSOR_NAME": "test_name",
            "COT_ACCESS": "test_access",
        }

        cot = djicot.functions.dji_uas_to_cot(data, config)
        assert cot is None

    def _test_dji_to_cot_missing_lat_lon(self):
        """Test dji_to_cot function with missing lat/lon."""
        data = bytearray(227)
        data[:2] = b"\x01\x00"  # frame_header
        data[2] = 0x01  # package_type
        data[3:5] = struct.pack("H", 227)  # package_length
        data[5:69] = b"serial_number".ljust(64, b"\x00")
        data[69:133] = b"device_type".ljust(64, b"\x00")
        data[133] = 8

        config = {
            "DEBUG": True,
            "COT_TYPE": "a-f-G-U-C",
            "COT_STALE": 600,
            "COT_HOST_ID": "test_host",
            "SENSOR_ID": "test_sensor",
            "SENSOR_SN": "test_sn",
            "SENSOR_TYPE": "test_type",
            "SENSOR_NAME": "test_name",
            "COT_ACCESS": "test_access",
        }

        cot = djicot.functions.dji_to_cot(data, config)
        assert cot is None


def test_parse_frame():
    test_data = b"\x100\x01\xe8\x00F4XF7249QM06Q26P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00DJI Mini 3 pro\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00I\x01\x81\xbd*I\xe1B@\x9a0j\x97\xda\x9f^\xc0\x01\x81\xbd*I\xe1B@\x9a0j\x97\xda\x9f^\xc0\x00\x00\x00\x00\x00\x00\x00\x00ffffff\xfe?\xce\xa7l:H\xe1B@\xc3q\x82\xdf\xda\x9f^\xc0\x00\x00\x00\x00\x00\xdd\xa2@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd7\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    dji_type, dji_data = djicot.dji_functions.parse_frame(test_data)
    assert dji_type == 1
    assert len(dji_data) == 227


def test_parse_data():
    test_data = b"\x100\x01\xe8\x00F4XF7249QM06Q26P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00DJI Mini 3 pro\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00I\x01\x81\xbd*I\xe1B@\x9a0j\x97\xda\x9f^\xc0\x01\x81\xbd*I\xe1B@\x9a0j\x97\xda\x9f^\xc0\x00\x00\x00\x00\x00\x00\x00\x00ffffff\xfe?\xce\xa7l:H\xe1B@\xc3q\x82\xdf\xda\x9f^\xc0\x00\x00\x00\x00\x00\xdd\xa2@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd7\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    dji_type, dji_data = djicot.dji_functions.parse_frame(test_data)
    assert dji_type == 1
    assert len(dji_data) == 227
    parsed_data = djicot.dji_functions.parse_data(dji_data)
    assert parsed_data.get("serial_number") == "F4XF7249QM06Q26P"
    assert parsed_data.get("device_type") == "DJI Mini 3 pro"
    assert parsed_data.get("device_type_8") == 73
    # assert parsed_data.get("app_lat") == 37.7749
    # assert parsed_data.get("app_lon") == -122.4194
    assert parsed_data.get("uas_lat") == 37.760045378237926
    assert parsed_data.get("uas_lon") == -122.49771676416495
    assert parsed_data.get("height") == 0.0
    assert parsed_data.get("altitude") == 1.9
    assert parsed_data.get("home_lat") == 37.76001673036045
    assert parsed_data.get("home_lon") == -122.49773395289144
    assert parsed_data.get("freq") == 2414.5
    assert parsed_data.get("speed_e") == 0.0
    assert parsed_data.get("speed_n") == 0.0
    assert parsed_data.get("speed_u") == 0.0
    assert parsed_data.get("rssi") == -41


def test_handle_frame():
    test_data = b"\x100\x01\xe8\x00F4XF7249QM06Q26P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00DJI Mini 3 pro\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00I\x01\x81\xbd*I\xe1B@\x9a0j\x97\xda\x9f^\xc0\x01\x81\xbd*I\xe1B@\x9a0j\x97\xda\x9f^\xc0\x00\x00\x00\x00\x00\x00\x00\x00ffffff\xfe?\xce\xa7l:H\xe1B@\xc3q\x82\xdf\xda\x9f^\xc0\x00\x00\x00\x00\x00\xdd\xa2@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd7\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    events = djicot.functions.handle_frame(test_data)
    assert len(events) == 3
    for event in events:
        event = event.decode("utf-8")
        print("-- EVENT --")
        print(event)
        assert "sensor_id" in event
        assert event.startswith("<?xml")
        assert event.endswith("</event>")
        assert "F4XF7249QM06Q26P" in event

        if ".uas" in event:
            assert "DJI.F4XF7249QM06Q26P.uas" in event
            assert "a-u-A-M-H-Q" in event
            assert "DJI Mini 3 pro" in event
            assert "freq=2414.5" in event
            assert 'rssi="-41"' in event

        if ".op" in event:
            assert "DJI.F4XF7249QM06Q26P.op" in event
            assert "a-u-G-U-C" in event
            assert "37.76" in event

        if ".home" in event:
            assert "DJI.F4XF7249QM06Q26P.home" in event
            assert "a-u-G-U-C" in event
            assert "37.76" in event


if __name__ == "__main__":
    unittest.main()
