"""Tests for Anthem AV Serial coordinator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import pytest

from custom_components.anthemav_serial.const import (
    DOMAIN,
)
from custom_components.anthemav_serial.coordinator import AnthemAVSerialCoordinator


@pytest.fixture
def mock_config_entry(
    hass: HomeAssistant,
    mock_config_entry_data: dict[str, Any],
    mock_config_entry_options: dict[str, Any],
) -> ConfigEntry:
    """Create a mock config entry."""
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
    return entry


async def test_coordinator_initialization(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_device_config: dict,
) -> None:
    """Test coordinator initializes correctly."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)

    assert coordinator.series == 'd2v'
    assert coordinator.zones == [1, 2, 3]
    assert 1 in coordinator.sources
    assert coordinator.sources[1] == 'CD'
    assert not coordinator.is_connected


async def test_coordinator_connect_success(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator connects successfully."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)

    result = await coordinator.async_connect()

    assert result is True
    assert coordinator.is_connected
    mock_get_async_amp_controller.assert_called_once()


async def test_coordinator_connect_failure(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_device_config: dict,
) -> None:
    """Test coordinator handles connection failure."""
    with patch(
        'custom_components.anthemav_serial.coordinator.get_async_amp_controller',
        new_callable=AsyncMock,
        return_value=None,
    ):
        coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
        result = await coordinator.async_connect()

    assert result is False
    assert not coordinator.is_connected


async def test_coordinator_update_data(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_amp: MagicMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator fetches zone data."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
    await coordinator.async_connect()

    data = await coordinator._async_update_data()

    assert 1 in data
    assert data[1]['power'] is True
    assert data[1]['volume'] == 0.5
    assert data[1]['mute'] is False


async def test_coordinator_set_power(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_amp: MagicMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator sets power correctly."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
    await coordinator.async_connect()

    await coordinator.async_set_power(1, True)

    mock_amp.set_power.assert_called_once_with(1, True)


async def test_coordinator_set_volume(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_amp: MagicMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator sets volume correctly."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
    await coordinator.async_connect()

    await coordinator.async_set_volume(1, 0.75)

    mock_amp.set_volume.assert_called_once_with(1, 0.75)


async def test_coordinator_set_mute(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_amp: MagicMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator sets mute correctly."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
    await coordinator.async_connect()

    await coordinator.async_set_mute(1, True)

    mock_amp.set_mute.assert_called_once_with(1, True)


async def test_coordinator_set_source(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_amp: MagicMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator sets source correctly."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
    await coordinator.async_connect()

    await coordinator.async_set_source(1, 2)

    mock_amp.set_source.assert_called_once_with(1, 2)


async def test_coordinator_disconnect(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_get_async_amp_controller: AsyncMock,
    mock_amp: MagicMock,
    mock_device_config: dict,
) -> None:
    """Test coordinator disconnects correctly."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)
    await coordinator.async_connect()

    await coordinator.async_disconnect()

    assert not coordinator.is_connected
    mock_amp.close.assert_called_once()


async def test_coordinator_operations_when_not_connected(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_device_config: dict,
) -> None:
    """Test coordinator handles operations when not connected."""
    coordinator = AnthemAVSerialCoordinator(hass, mock_config_entry)

    # these should not raise, just log warnings
    await coordinator.async_set_power(1, True)
    await coordinator.async_set_volume(1, 0.5)
    await coordinator.async_set_mute(1, True)
    await coordinator.async_set_source(1, 1)
    await coordinator.async_volume_up(1)
    await coordinator.async_volume_down(1)

    assert not coordinator.is_connected
