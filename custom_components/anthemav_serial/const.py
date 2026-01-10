"""Constants for the Anthem AV Serial integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final[str] = 'anthemav_serial'

# Configuration keys
CONF_SERIAL_CONFIG: Final[str] = 'serial_config'
CONF_SERIAL_NUMBER: Final[str] = 'serial_number'
CONF_SERIES: Final[str] = 'series'
CONF_SOURCES: Final[str] = 'sources'
CONF_ZONES: Final[str] = 'zones'
CONF_MAX_VOLUME: Final[str] = 'max_volume'

# Defaults
DEFAULT_NAME: Final[str] = 'Anthem Receiver'
DEFAULT_SERIAL_NUMBER: Final[str] = '000000'
DEFAULT_SERIES: Final[str] = 'd2v'
DEFAULT_SCAN_INTERVAL: Final[int] = 10
DEFAULT_MAX_VOLUME: Final[float] = 0.6

# Supported series (Gen1 RS232 protocol)
SUPPORTED_SERIES: Final[list[str]] = [
    'd1',
    'd2',
    'd2v',
    'avm20',
    'avm30',
    'avm50',
    'mrx',
]
