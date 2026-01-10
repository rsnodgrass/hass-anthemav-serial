"""Tests for Anthem AV Serial media player."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.anthemav_serial.const import (
    CONF_SERIAL_NUMBER,
    CONF_SERIES,
    DEFAULT_MAX_VOLUME,
    DOMAIN,
)
from custom_components.anthemav_serial.coordinator import AnthemAVSerialCoordinator
from custom_components.anthemav_serial.media_player import AnthemAVSerialMediaPlayer


@pytest.fixture
def mock_coordinator(
    hass: HomeAssistant,
    mock_amp: MagicMock,
) -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock(spec=AnthemAVSerialCoordinator)
    coordinator.sources = {1: 'CD', 2: 'Tuner', 3: 'Video 1'}
    coordinator.zones = [1, 2, 3]
    coordinator.series = 'd2v'
    coordinator.data = {
        1: {'power': True, 'volume': 0.5, 'mute': False, 'source': 1},
        2: {'power': False, 'volume': 0.3, 'mute': True, 'source': 2},
        3: {'power': True, 'volume': 0.7, 'mute': False, 'source': 3},
    }
    coordinator.async_set_power = AsyncMock()
    coordinator.async_set_volume = AsyncMock()
    coordinator.async_volume_up = AsyncMock()
    coordinator.async_volume_down = AsyncMock()
    coordinator.async_set_mute = AsyncMock()
    coordinator.async_set_source = AsyncMock()
    return coordinator


@pytest.fixture
def media_player(mock_coordinator: MagicMock) -> AnthemAVSerialMediaPlayer:
    """Create a media player entity for testing."""
    return AnthemAVSerialMediaPlayer(
        coordinator=mock_coordinator,
        serial_number='123456',
        series='d2v',
        zone_id=1,
        zone_name='Main Zone',
        max_volume=DEFAULT_MAX_VOLUME,
    )


def test_media_player_unique_id(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test unique ID is generated correctly."""
    assert media_player.unique_id == f'{DOMAIN}_123456_1'


def test_media_player_name(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test entity name is set correctly."""
    assert media_player.name == 'Main Zone'


def test_media_player_device_info(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test device info is generated correctly."""
    device_info = media_player.device_info

    assert device_info['identifiers'] == {(DOMAIN, '123456')}
    assert device_info['manufacturer'] == 'Anthem'
    assert device_info['model'] == 'D2V'
    assert device_info['serial_number'] == '123456'


def test_media_player_state_on(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test state returns ON when powered on."""
    assert media_player.state == MediaPlayerState.ON


def test_media_player_state_off(
    mock_coordinator: MagicMock,
) -> None:
    """Test state returns OFF when powered off."""
    player = AnthemAVSerialMediaPlayer(
        coordinator=mock_coordinator,
        serial_number='123456',
        series='d2v',
        zone_id=2,
        zone_name='Zone 2',
        max_volume=DEFAULT_MAX_VOLUME,
    )
    assert player.state == MediaPlayerState.OFF


def test_media_player_volume_level(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test volume level is returned correctly."""
    assert media_player.volume_level == 0.5


def test_media_player_is_volume_muted(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test mute state is returned correctly."""
    assert media_player.is_volume_muted is False


def test_media_player_source(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test current source is returned correctly."""
    assert media_player.source == 'CD'


def test_media_player_source_list(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test source list contains all sources."""
    sources = media_player.source_list
    assert 'CD' in sources
    assert 'Tuner' in sources
    assert 'Video 1' in sources


async def test_media_player_turn_on(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test turn on calls coordinator."""
    await media_player.async_turn_on()
    media_player.coordinator.async_set_power.assert_called_once_with(1, True)


async def test_media_player_turn_off(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test turn off calls coordinator."""
    await media_player.async_turn_off()
    media_player.coordinator.async_set_power.assert_called_once_with(1, False)


async def test_media_player_set_volume(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test set volume calls coordinator."""
    await media_player.async_set_volume_level(0.4)
    media_player.coordinator.async_set_volume.assert_called_once_with(1, 0.4)


async def test_media_player_set_volume_exceeds_max(
    media_player: AnthemAVSerialMediaPlayer,
) -> None:
    """Test set volume is limited to max volume."""
    await media_player.async_set_volume_level(0.9)
    # should be limited to max_volume (0.6)
    media_player.coordinator.async_set_volume.assert_called_once_with(1, 0.6)


async def test_media_player_volume_up(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test volume up calls coordinator."""
    await media_player.async_volume_up()
    media_player.coordinator.async_volume_up.assert_called_once_with(1)


async def test_media_player_volume_down(
    media_player: AnthemAVSerialMediaPlayer,
) -> None:
    """Test volume down calls coordinator."""
    await media_player.async_volume_down()
    media_player.coordinator.async_volume_down.assert_called_once_with(1)


async def test_media_player_mute(media_player: AnthemAVSerialMediaPlayer) -> None:
    """Test mute calls coordinator."""
    await media_player.async_mute_volume(True)
    media_player.coordinator.async_set_mute.assert_called_once_with(1, True)


async def test_media_player_select_source(
    media_player: AnthemAVSerialMediaPlayer,
) -> None:
    """Test select source calls coordinator."""
    await media_player.async_select_source('Tuner')
    media_player.coordinator.async_set_source.assert_called_once_with(1, 2)


async def test_media_player_select_invalid_source(
    media_player: AnthemAVSerialMediaPlayer,
) -> None:
    """Test select invalid source does not call coordinator."""
    await media_player.async_select_source('Invalid Source')
    media_player.coordinator.async_set_source.assert_not_called()
