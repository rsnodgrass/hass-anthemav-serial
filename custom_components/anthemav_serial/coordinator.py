"""DataUpdateCoordinator for Anthem AV Serial integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from anthemav_serial import get_async_amp_controller
from anthemav_serial.config import DEVICE_CONFIG

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SERIES,
    CONF_SOURCES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

LOG = logging.getLogger(__name__)


class AnthemAVSerialCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Coordinator for managing Anthem AV Serial device data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self._amp: Any | None = None
        self._port: str = config_entry.data[CONF_PORT]
        self._series: str = config_entry.data[CONF_SERIES]
        self._sources: dict[int, str] = {}
        self._zones: list[int] = []
        self._connected: bool = False

        scan_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            LOG,
            name=f'{DOMAIN}_{self._port}',
            update_interval=timedelta(seconds=scan_interval),
        )

        # load source configuration from the anthemav_serial library
        self._load_device_config()

    def _load_device_config(self) -> None:
        """Load device configuration from anthemav_serial library."""
        if self._series in DEVICE_CONFIG:
            device_conf = DEVICE_CONFIG[self._series]
            # extract sources
            raw_sources = device_conf.get(CONF_SOURCES, {})
            for source_id, source_data in raw_sources.items():
                if isinstance(source_data, dict) and 'name' in source_data:
                    self._sources[int(source_id)] = source_data['name']
                elif isinstance(source_data, str):
                    self._sources[int(source_id)] = source_data

            # default to 3 zones for most Anthem receivers
            self._zones = [1, 2, 3]
            LOG.debug(
                'Loaded config for %s: sources=%s', self._series, self._sources
            )

    @property
    def amp(self) -> Any | None:
        """Return the amp controller instance."""
        return self._amp

    @property
    def sources(self) -> dict[int, str]:
        """Return source name mapping."""
        return self._sources

    @property
    def zones(self) -> list[int]:
        """Return list of zone IDs."""
        return self._zones

    @property
    def series(self) -> str:
        """Return the device series."""
        return self._series

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected

    async def async_connect(self) -> bool:
        """Establish connection to the Anthem device."""
        if self._connected and self._amp is not None:
            return True

        try:
            LOG.info('Connecting to Anthem %s at %s', self._series, self._port)
            self._amp = await get_async_amp_controller(
                self._series,
                self._port,
                self.hass.loop,
            )

            if self._amp is None:
                LOG.error('Failed to create amp controller for %s', self._port)
                return False

            self._connected = True
            LOG.info('Connected to Anthem %s at %s', self._series, self._port)
            return True

        except Exception:
            LOG.exception('Error connecting to Anthem at %s', self._port)
            self._connected = False
            return False

    async def async_disconnect(self) -> None:
        """Disconnect from the Anthem device."""
        if self._amp is not None:
            try:
                # the anthemav_serial library may have a close method
                if hasattr(self._amp, 'close'):
                    await self._amp.close()
                elif hasattr(self._amp, 'disconnect'):
                    await self._amp.disconnect()
            except Exception:
                LOG.exception('Error disconnecting from Anthem device')
            finally:
                self._amp = None
                self._connected = False

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Fetch data from the Anthem device."""
        if not self._connected:
            if not await self.async_connect():
                raise UpdateFailed('Failed to connect to Anthem device')

        zone_data: dict[int, dict[str, Any]] = {}

        for zone_id in self._zones:
            try:
                if self._amp is not None:
                    status = await self._amp.zone_status(zone_id)
                    if status:
                        zone_data[zone_id] = status
                    else:
                        zone_data[zone_id] = {}
            except Exception:
                LOG.exception('Error fetching status for zone %s', zone_id)
                zone_data[zone_id] = {}

        LOG.debug('Updated zone data: %s', zone_data)
        return zone_data

    async def async_set_power(self, zone: int, power: bool) -> None:
        """Set power state for a zone."""
        if self._amp is None:
            LOG.warning('Cannot set power: not connected')
            return
        try:
            await self._amp.set_power(zone, power)
            await self.async_request_refresh()
        except Exception:
            LOG.exception('Error setting power for zone %s', zone)

    async def async_set_volume(self, zone: int, volume: float) -> None:
        """Set volume level for a zone."""
        if self._amp is None:
            LOG.warning('Cannot set volume: not connected')
            return
        try:
            await self._amp.set_volume(zone, volume)
            await self.async_request_refresh()
        except Exception:
            LOG.exception('Error setting volume for zone %s', zone)

    async def async_volume_up(self, zone: int) -> None:
        """Increase volume for a zone."""
        if self._amp is None:
            LOG.warning('Cannot increase volume: not connected')
            return
        try:
            await self._amp.volume_up(zone)
            await self.async_request_refresh()
        except Exception:
            LOG.exception('Error increasing volume for zone %s', zone)

    async def async_volume_down(self, zone: int) -> None:
        """Decrease volume for a zone."""
        if self._amp is None:
            LOG.warning('Cannot decrease volume: not connected')
            return
        try:
            await self._amp.volume_down(zone)
            await self.async_request_refresh()
        except Exception:
            LOG.exception('Error decreasing volume for zone %s', zone)

    async def async_set_mute(self, zone: int, mute: bool) -> None:
        """Set mute state for a zone."""
        if self._amp is None:
            LOG.warning('Cannot set mute: not connected')
            return
        try:
            await self._amp.set_mute(zone, mute)
            await self.async_request_refresh()
        except Exception:
            LOG.exception('Error setting mute for zone %s', zone)

    async def async_set_source(self, zone: int, source_id: int) -> None:
        """Set input source for a zone."""
        if self._amp is None:
            LOG.warning('Cannot set source: not connected')
            return
        try:
            await self._amp.set_source(zone, source_id)
            await self.async_request_refresh()
        except Exception:
            LOG.exception('Error setting source for zone %s', zone)
