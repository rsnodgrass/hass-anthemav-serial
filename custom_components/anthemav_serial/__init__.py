"""Home Assistant Anthem AV RS232 Serial integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AnthemAVSerialCoordinator

LOG = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

type AnthemAVSerialConfigEntry = ConfigEntry[AnthemAVSerialCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: AnthemAVSerialConfigEntry
) -> bool:
    """Set up Anthem AV Serial from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = AnthemAVSerialCoordinator(hass, entry)

    # initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # store coordinator in runtime data
    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # reload on options update
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    LOG.info(
        'Anthem AV Serial integration setup complete for %s', entry.data[CONF_PORT]
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: AnthemAVSerialConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = entry.runtime_data
        await coordinator.async_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        LOG.info('Anthem AV Serial integration unloaded for %s', entry.data[CONF_PORT])

    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant, entry: AnthemAVSerialConfigEntry
) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
