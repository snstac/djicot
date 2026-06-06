# Configuration

DJICOT's configuration parameters can be set two ways:

1. In an INI-style configuration file. (ex. ``djicot -c config.ini``)
2. As environment variables. (ex. ``export DEBUG=1; djicot``)

DJICOT has the following built-in configuration parameters:

* **`FEED_URL`**:
    * Default: ``tcp://192.168.1.10:41030``

    AntSDR source URL. DJICOT selects the input worker from the URL:

    * ``tcp://host:41030`` — binary DJI Drone ID frames (default AntSDR port)
    * ``tcp://host:52002`` — text CSV ``dji_O,...`` debug stream
    * ``file:///path/to/log`` — offline replay of a captured text log

* **`FEED_FORMAT`**:
    * Default: unset (auto-detect from ``FEED_URL``)

    Set to ``text`` to force the text CSV parser when using a non-standard TCP port.

* **`COT_TYPE`**:
    * Default: ``a-u-A-M-H-Q``

    Cursor on Target (CoT) Event type. Default is unknown rotor-wing UAV.

* **`SENSOR_LAT`**:
    * Default: ``0.0``

    Latitude of AntSDR sensor. If set, sends periodic sensor CoT & used for 'Range' detections.

* **`SENSOR_LON`**:
    * Default: ``0.0``

    Longitude of AntSDR sensor. If set, sends periodic sensor CoT & used for 'Range' detections.

* **`SENSOR_ID`**:
    * Default: ``DJICOT``

    Unique identifier for sensor. Added as sensor metadata in __cuas CoT Element.

* **`SENSOR_COT_TYPE`**:
    * Default: ``a-f-G-E-S-E``

    Cursor on Target (CoT) Event type for sensor.

* **`HIDE_INVALID_DATA`**:
    * Default: ``0``

    When set, suppresses CoT for legs with invalid or missing coordinates.

Additional configuration parameters, including TAK Server TLS, certificate enrollment, and ``PYTAK_NO_HELLO``, are included in the [PyTAK Configuration](https://pytak.readthedocs.io/en/latest/configuration/) documentation.

See also: [example-config.ini](https://github.com/snstac/djicot/blob/main/example-config.ini).
