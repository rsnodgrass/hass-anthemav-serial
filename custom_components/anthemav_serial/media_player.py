"""Media Player entity for Anthem A/V Receivers and Processors via RS232."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MAX_VOLUME,
    CONF_SERIAL_NUMBER,
    CONF_SERIES,
    DEFAULT_MAX_VOLUME,
    DOMAIN,
)
from .coordinator import AnthemAVSerialCoordinator

LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Anthem media player from a config entry."""
    coordinator: AnthemAVSerialCoordinator = hass.data[DOMAIN][entry.entry_id]

    serial_number = entry.data.get(CONF_SERIAL_NUMBER, '000000')
    series = entry.data.get(CONF_SERIES, 'd2v')
    max_volume = entry.options.get(CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME)

    entities: list[AnthemAVSerialMediaPlayer] = []

    for zone_id in coordinator.zones:
        zone_name = 'Main Zone' if zone_id == 1 else f'Zone {zone_id}'
        entity = AnthemAVSerialMediaPlayer(
            coordinator=coordinator,
            serial_number=serial_number,
            series=series,
            zone_id=zone_id,
            zone_name=zone_name,
            max_volume=max_volume,
        )
        entities.append(entity)
        LOG.info('Adding Anthem %s zone %s (%s)', series, zone_id, zone_name)

    async_add_entities(entities)
    LOG.info(
        'Anthem %s media player setup complete with %s zones', series, len(entities)
    )


class AnthemAVSerialMediaPlayer(
    CoordinatorEntity[AnthemAVSerialCoordinator], MediaPlayerEntity
):
    """Entity for controlling Anthem AV receiver zones."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self,
        coordinator: AnthemAVSerialCoordinator,
        serial_number: str,
        series: str,
        zone_id: int,
        zone_name: str,
        max_volume: float,
    ) -> None:
        """Initialize the media player entity."""
        super().__init__(coordinator)

        self._serial_number = serial_number
        self._series = series
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._max_volume = max_volume

        # unique id matches original pattern to preserve entity ids
        self._attr_unique_id = f'{DOMAIN}_{serial_number}_{zone_id}'
        self._attr_name = zone_name

        # build source name to id mapping
        self._source_name_to_id: dict[str, int] = {}
        for source_id, source_name in coordinator.sources.items():
            self._source_name_to_id[source_name] = source_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f'Anthem {self._series.upper()}',
            manufacturer='Anthem',
            model=self._series.upper(),
            serial_number=self._serial_number,
        )

    @property
    def _zone_data(self) -> dict[str, Any]:
        """Return current zone data from coordinator."""
        if self.coordinator.data is None:
            return {}
        return self.coordinator.data.get(self._zone_id, {})

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the current state."""
        power = self._zone_data.get('power')
        if power is True:
            return MediaPlayerState.ON
        if power is False:
            return MediaPlayerState.OFF
        return None

    @property
    def volume_level(self) -> float | None:
        """Return the current volume level (0.0 to 1.0)."""
        volume = self._zone_data.get('volume')
        if volume is None:
            return None
        return float(volume)

    @property
    def is_volume_muted(self) -> bool | None:
        """Return whether the device is muted."""
        mute = self._zone_data.get('mute')
        if mute is None:
            # if powered off, consider muted
            if self._zone_data.get('power') is False:
                return True
            return None
        return bool(mute)

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        source_id = self._zone_data.get('source')
        if source_id is None:
            return None

        source_name = self.coordinator.sources.get(source_id)
        if source_name is None:
            # dynamically add source if not in configuration
            source_name = f'Source {source_id}'
            self.coordinator.sources[source_id] = source_name
            self._source_name_to_id[source_name] = source_id

        return source_name

    @property
    def source_list(self) -> list[str]:
        """Return all available input sources."""
        return list(self._source_name_to_id.keys())

    async def async_turn_on(self) -> None:
        """Turn on the zone."""
        LOG.info('Turning on %s (zone %s)', self._zone_name, self._zone_id)
        await self.coordinator.async_set_power(self._zone_id, True)

    async def async_turn_off(self) -> None:
        """Turn off the zone."""
        LOG.info('Turning off %s (zone %s)', self._zone_name, self._zone_id)
        await self.coordinator.async_set_power(self._zone_id, False)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        # enforce maximum volume limit
        if volume > self._max_volume:
            LOG.warning(
                'Volume %s exceeds max %s for %s, limiting',
                volume,
                self._max_volume,
                self._zone_name,
            )
            volume = self._max_volume

        LOG.info(
            'Setting %s (zone %s) volume to %s', self._zone_name, self._zone_id, volume
        )
        await self.coordinator.async_set_volume(self._zone_id, volume)

    async def async_volume_up(self) -> None:
        """Increase volume."""
        LOG.debug('Increasing volume for %s (zone %s)', self._zone_name, self._zone_id)
        await self.coordinator.async_volume_up(self._zone_id)

    async def async_volume_down(self) -> None:
        """Decrease volume."""
        LOG.debug('Decreasing volume for %s (zone %s)', self._zone_name, self._zone_id)
        await self.coordinator.async_volume_down(self._zone_id)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the volume."""
        LOG.info(
            'Setting mute to %s for %s (zone %s)', mute, self._zone_name, self._zone_id
        )
        await self.coordinator.async_set_mute(self._zone_id, mute)

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        source_id = self._source_name_to_id.get(source)
        if source_id is None:
            LOG.warning(
                'Source "%s" not found for %s (zone %s)',
                source,
                self._zone_name,
                self._zone_id,
            )
            return

        LOG.info(
            'Selecting source "%s" (id=%s) for %s (zone %s)',
            source,
            source_id,
            self._zone_name,
            self._zone_id,
        )
        await self.coordinator.async_set_source(self._zone_id, source_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
