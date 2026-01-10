"""Tests for Anthem AV Serial diagnostics."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
import pytest

from custom_components.anthemav_serial.const import (
    CONF_SERIAL_NUMBER,
    DOMAIN,
)
from custom_components.anthemav_serial.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create a mock coordinator for diagnostics testing."""
    coordinator = MagicMock()
    coordinator.series = 'd2v'
    coordinator.is_connected = True
    coordinator.zones = [1, 2, 3]
    coordinator.sources = {1: 'CD', 2: 'Tuner'}
    coordinator.last_update_success = True
    coordinator.update_interval = timedelta(seconds=10)
    coordinator.data = {
        1: {'power': True, 'volume': 0.5},
        2: {'power': False, 'volume': 0.3},
    }
    return coordinator


async def test_diagnostics_redacts_sensitive_data(
    hass: HomeAssistant,
    mock_coordinator: MagicMock,
    mock_config_entry_data: dict[str, Any],
    mock_config_entry_options: dict[str, Any],
) -> None:
    """Test diagnostics redacts sensitive information."""
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title='Test Anthem',
        data=mock_config_entry_data,
        source='user',
        options=mock_config_entry_options,
        unique_id='/dev/ttyUSB0_123456',
        entry_id='test_entry_id',
    )

    hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # check that sensitive keys are redacted
    assert diagnostics['config_entry']['data'][CONF_PORT] == '**REDACTED**'
    assert diagnostics['config_entry']['data'][CONF_SERIAL_NUMBER] == '**REDACTED**'


async def test_diagnostics_includes_coordinator_info(
    hass: HomeAssistant,
    mock_coordinator: MagicMock,
    mock_config_entry_data: dict[str, Any],
    mock_config_entry_options: dict[str, Any],
) -> None:
    """Test diagnostics includes coordinator information."""
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title='Test Anthem',
        data=mock_config_entry_data,
        source='user',
        options=mock_config_entry_options,
        unique_id='/dev/ttyUSB0_123456',
        entry_id='test_entry_id',
    )

    hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics['coordinator']['series'] == 'd2v'
    assert diagnostics['coordinator']['is_connected'] is True
    assert diagnostics['coordinator']['zones'] == [1, 2, 3]
    assert diagnostics['coordinator']['update_interval'] == 10.0


async def test_diagnostics_includes_zone_data(
    hass: HomeAssistant,
    mock_coordinator: MagicMock,
    mock_config_entry_data: dict[str, Any],
    mock_config_entry_options: dict[str, Any],
) -> None:
    """Test diagnostics includes zone data."""
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title='Test Anthem',
        data=mock_config_entry_data,
        source='user',
        options=mock_config_entry_options,
        unique_id='/dev/ttyUSB0_123456',
        entry_id='test_entry_id',
    )

    hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert 1 in diagnostics['zone_data']
    assert diagnostics['zone_data'][1]['power'] is True
    assert diagnostics['zone_data'][1]['volume'] == 0.5
