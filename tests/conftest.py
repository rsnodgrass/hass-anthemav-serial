"""Fixtures for Anthem AV Serial tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_PORT, CONF_SCAN_INTERVAL
import pytest

from custom_components.anthemav_serial.const import (
    CONF_MAX_VOLUME,
    CONF_SERIAL_NUMBER,
    CONF_SERIES,
    DEFAULT_MAX_VOLUME,
    DEFAULT_SCAN_INTERVAL,
)


@pytest.fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Return mock config entry data."""
    return {
        CONF_PORT: '/dev/ttyUSB0',
        CONF_SERIES: 'd2v',
        CONF_SERIAL_NUMBER: '123456',
    }


@pytest.fixture
def mock_config_entry_options() -> dict[str, Any]:
    """Return mock config entry options."""
    return {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_MAX_VOLUME: DEFAULT_MAX_VOLUME,
    }


@pytest.fixture
def mock_amp() -> MagicMock:
    """Create a mock amp controller."""
    amp = MagicMock()
    amp.zone_status = AsyncMock(
        return_value={
            'power': True,
            'volume': 0.5,
            'mute': False,
            'source': 1,
        }
    )
    amp.set_power = AsyncMock()
    amp.set_volume = AsyncMock()
    amp.volume_up = AsyncMock()
    amp.volume_down = AsyncMock()
    amp.set_mute = AsyncMock()
    amp.set_source = AsyncMock()
    amp.close = AsyncMock()
    return amp


@pytest.fixture
def mock_get_async_amp_controller(mock_amp: MagicMock) -> Generator[AsyncMock]:
    """Mock the get_async_amp_controller function."""
    with patch(
        'custom_components.anthemav_serial.coordinator.get_async_amp_controller',
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_amp
        yield mock_get


@pytest.fixture
def mock_device_config() -> Generator[dict]:
    """Mock the DEVICE_CONFIG from anthemav_serial."""
    device_config = {
        'd2v': {
            'sources': {
                1: {'name': 'CD'},
                2: {'name': 'Tuner'},
                3: {'name': 'Video 1'},
                4: {'name': 'Video 2'},
            }
        },
        'd2': {
            'sources': {
                1: {'name': 'CD'},
                2: {'name': 'Tuner'},
            }
        },
    }
    with patch(
        'custom_components.anthemav_serial.coordinator.DEVICE_CONFIG',
        device_config,
    ):
        yield device_config
