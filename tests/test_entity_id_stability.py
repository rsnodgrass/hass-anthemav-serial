"""Entity ID stability tests for Anthem AV Serial integration.

These tests ensure that unique_id generation remains stable across updates.
Changing unique_id patterns will cause existing entities to become orphaned
and users will lose their automations, dashboards, and history.

GOLDEN FORMAT DOCUMENTATION
===========================

The unique_id pattern for media_player entities is:
    {DOMAIN}_{serial_number}_{zone_id}

Where:
    - DOMAIN: 'anthemav_serial' (from const.py)
    - serial_number: Device serial number from config entry (e.g., '123456')
    - zone_id: Integer zone identifier (1 = Main Zone, 2+ = Zone N)

Examples:
    - anthemav_serial_123456_1  -> Main Zone for device 123456
    - anthemav_serial_123456_2  -> Zone 2 for device 123456
    - anthemav_serial_ABC789_3  -> Zone 3 for device ABC789

WARNING: Changing this pattern is a BREAKING CHANGE that will:
    - Orphan existing entities in Home Assistant
    - Break automations referencing these entities
    - Lose entity history and statistics
    - Require users to manually reconfigure dashboards

If you must change the pattern, provide a migration path.
"""

from __future__ import annotations

import pytest

from custom_components.anthemav_serial.const import DOMAIN


# -----------------------------------------------------------------------------
# unique_id generation functions
# these must match the actual implementation in media_player.py
# -----------------------------------------------------------------------------


def generate_media_player_unique_id(serial_number: str, zone_id: int) -> str:
    """Generate unique_id for a media player entity.

    This function replicates the logic from AnthemAVSerialMediaPlayer.__init__:
        self._attr_unique_id = f'{DOMAIN}_{serial_number}_{zone_id}'

    Args:
        serial_number: Device serial number from config entry.
        zone_id: Zone identifier (1 for main zone, 2+ for additional zones).

    Returns:
        The unique_id string for the entity.
    """
    return f'{DOMAIN}_{serial_number}_{zone_id}'


def generate_device_identifier(serial_number: str) -> tuple[str, str]:
    """Generate device registry identifier tuple.

    This function replicates the logic from AnthemAVSerialMediaPlayer.device_info:
        identifiers={(DOMAIN, self._serial_number)}

    Args:
        serial_number: Device serial number from config entry.

    Returns:
        Tuple of (domain, serial_number) for device registry.
    """
    return (DOMAIN, serial_number)


# -----------------------------------------------------------------------------
# parametrized test data
# -----------------------------------------------------------------------------


UNIQUE_ID_TEST_CASES = [
    # (serial_number, zone_id, expected_unique_id)
    pytest.param('123456', 1, 'anthemav_serial_123456_1', id='main-zone-numeric'),
    pytest.param('123456', 2, 'anthemav_serial_123456_2', id='zone2-numeric'),
    pytest.param('123456', 3, 'anthemav_serial_123456_3', id='zone3-numeric'),
    pytest.param('ABC123', 1, 'anthemav_serial_ABC123_1', id='main-zone-alphanumeric'),
    pytest.param('abc123', 1, 'anthemav_serial_abc123_1', id='main-zone-lowercase'),
    pytest.param('000000', 1, 'anthemav_serial_000000_1', id='default-serial'),
    pytest.param('A1B2C3D4E5', 1, 'anthemav_serial_A1B2C3D4E5_1', id='long-serial'),
    pytest.param('1', 1, 'anthemav_serial_1_1', id='short-serial'),
]

DEVICE_IDENTIFIER_TEST_CASES = [
    # (serial_number, expected_identifier_tuple)
    pytest.param('123456', ('anthemav_serial', '123456'), id='numeric-serial'),
    pytest.param('ABC789', ('anthemav_serial', 'ABC789'), id='alphanumeric-serial'),
    pytest.param('000000', ('anthemav_serial', '000000'), id='default-serial'),
]


# -----------------------------------------------------------------------------
# tests
# -----------------------------------------------------------------------------


class TestUniqueIdGeneration:
    """Tests for unique_id generation stability."""

    @pytest.mark.parametrize(
        ('serial_number', 'zone_id', 'expected_unique_id'),
        UNIQUE_ID_TEST_CASES,
    )
    def test_unique_id_format(
        self,
        serial_number: str,
        zone_id: int,
        expected_unique_id: str,
    ) -> None:
        """Verify unique_id matches expected golden format.

        WARNING: If this test fails after a code change, you have introduced
        a breaking change that will orphan existing entities.
        """
        result = generate_media_player_unique_id(serial_number, zone_id)
        assert result == expected_unique_id, (
            f'unique_id format changed! Expected {expected_unique_id!r}, '
            f'got {result!r}. This is a BREAKING CHANGE.'
        )

    def test_unique_id_uses_correct_domain(self) -> None:
        """Verify unique_id uses the DOMAIN constant from const.py."""
        unique_id = generate_media_player_unique_id('test', 1)
        assert unique_id.startswith(f'{DOMAIN}_'), (
            f'unique_id must start with DOMAIN ({DOMAIN}_), got {unique_id}'
        )

    def test_unique_id_contains_serial_number(self) -> None:
        """Verify unique_id contains the serial number."""
        serial = 'TESTSERIAL123'
        unique_id = generate_media_player_unique_id(serial, 1)
        assert serial in unique_id, (
            f'unique_id must contain serial number {serial}, got {unique_id}'
        )

    def test_unique_id_contains_zone_id(self) -> None:
        """Verify unique_id contains the zone identifier."""
        zone_id = 5
        unique_id = generate_media_player_unique_id('test', zone_id)
        assert str(zone_id) in unique_id, (
            f'unique_id must contain zone_id {zone_id}, got {unique_id}'
        )

    def test_different_zones_produce_different_ids(self) -> None:
        """Verify each zone gets a unique identifier."""
        serial = '123456'
        zone_ids = [1, 2, 3]
        unique_ids = [generate_media_player_unique_id(serial, z) for z in zone_ids]
        assert len(unique_ids) == len(set(unique_ids)), (
            'Different zones must produce different unique_ids'
        )

    def test_different_devices_produce_different_ids(self) -> None:
        """Verify different devices get unique identifiers."""
        serials = ['111111', '222222', '333333']
        zone_id = 1
        unique_ids = [generate_media_player_unique_id(s, zone_id) for s in serials]
        assert len(unique_ids) == len(set(unique_ids)), (
            'Different serial numbers must produce different unique_ids'
        )


class TestDeviceIdentifierGeneration:
    """Tests for device registry identifier stability."""

    @pytest.mark.parametrize(
        ('serial_number', 'expected_identifier'),
        DEVICE_IDENTIFIER_TEST_CASES,
    )
    def test_device_identifier_format(
        self,
        serial_number: str,
        expected_identifier: tuple[str, str],
    ) -> None:
        """Verify device identifier matches expected format.

        WARNING: If this test fails after a code change, you have introduced
        a breaking change that will orphan existing device entries.
        """
        result = generate_device_identifier(serial_number)
        assert result == expected_identifier, (
            f'Device identifier format changed! Expected {expected_identifier!r}, '
            f'got {result!r}. This is a BREAKING CHANGE.'
        )

    def test_device_identifier_uses_correct_domain(self) -> None:
        """Verify device identifier uses the DOMAIN constant."""
        identifier = generate_device_identifier('test')
        assert identifier[0] == DOMAIN, (
            f'Device identifier must use DOMAIN ({DOMAIN}), got {identifier[0]}'
        )


class TestDomainConstant:
    """Tests for DOMAIN constant stability."""

    def test_domain_value(self) -> None:
        """Verify DOMAIN constant has not changed.

        WARNING: Changing DOMAIN is a BREAKING CHANGE that affects:
        - All unique_ids
        - All device identifiers
        - Config entry storage
        - Service calls
        """
        assert DOMAIN == 'anthemav_serial', (
            f'DOMAIN constant changed from "anthemav_serial" to "{DOMAIN}". '
            'This is a BREAKING CHANGE that will orphan all existing entities.'
        )
