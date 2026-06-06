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

"""DJICOT Class Tests."""

import asyncio
from configparser import ConfigParser

import pytest

from djicot.classes import DJIWorker, TextNetWorker
from djicot.constants import DEFAULT_SENSOR_COT_TYPE, DEFAULT_COT_TYPE


@pytest.fixture
def config():
    config_parser = ConfigParser()
    config_parser.read_dict(
        {
            "DEFAULT": {
                "SENSOR_LAT": "37.76",
                "SENSOR_LON": "-122.4975",
                "HIDE_INVALID_DATA": "0",
            }
        }
    )
    return config_parser["DEFAULT"]


@pytest.fixture
def real_queue():
    return asyncio.Queue()


@pytest.fixture
def real_queue2():
    return asyncio.Queue()


@pytest.fixture
def real_worker(real_queue, real_queue2, config):
    return DJIWorker(real_queue, config, real_queue2)


@pytest.mark.asyncio
async def test_handle_data_with_invalid_data(real_worker, real_queue):
    data = b"<dji_data/>"
    await real_worker.handle_data(data)
    event = await real_queue.get()
    assert b"DJI" in event


@pytest.mark.asyncio
async def test_handle_text_line(real_worker, real_queue, config):
    line = (
        "dji_O,2/3,5756.5,-112,DJI Mini 2(63),3NZCHBL003AUDW,"
        "0.000000,0.000000,-122.497677,37.760034,0.000000,0.000000,"
        "0.00|0.00,0.00|0.00|0.00,1773352625843;"
    )
    await real_worker.handle_data(line)
    event = await real_queue.get()
    assert b"DJI.3NZCHBL003AUDW.uas" in event
    assert DEFAULT_COT_TYPE.encode("UTF-8") in event


@pytest.mark.asyncio
async def test_hello_event(real_worker, real_queue):
    result = await real_worker.hello_event(init=True)
    event = await real_queue.get()
    assert event is not None
    assert b"CUAS" in event
    assert result is None


@pytest.mark.asyncio
async def test_hello_event_respects_pytak_no_hello(real_queue, real_queue2):
    config_parser = ConfigParser()
    config_parser.read_dict({"DEFAULT": {"PYTAK_NO_HELLO": "1"}})
    worker = DJIWorker(real_queue, config_parser["DEFAULT"], real_queue2)
    await worker.hello_event(init=True)
    assert real_queue.empty()


def test_text_net_worker_feed_dispatch(config):
    config_parser = ConfigParser()
    config_parser.read_dict(
        {
            "DEFAULT": {
                **dict(config.items()),
                "FEED_URL": "tcp://127.0.0.1:52002",
            }
        }
    )
    worker = TextNetWorker(asyncio.Queue(), config_parser["DEFAULT"])
    assert worker.__class__.__name__ == "TextNetWorker"
