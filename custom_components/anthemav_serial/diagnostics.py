"""Diagnostics support for Anthem AV Serial integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant

from .const import CONF_SERIAL_NUMBER, DOMAIN
from .coordinator import AnthemAVSerialCoordinator

# keys to redact from diagnostics output
REDACT_KEYS = {CONF_SERIAL_NUMBER, CONF_PORT}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: AnthemAVSerialCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        'config_entry': {
            'entry_id': entry.entry_id,
            'version': entry.version,
            'domain': entry.domain,
            'title': entry.title,
            'data': async_redact_data(dict(entry.data), REDACT_KEYS),
            'options': dict(entry.options),
        },
        'coordinator': {
            'series': coordinator.series,
            'is_connected': coordinator.is_connected,
            'zones': coordinator.zones,
            'sources': coordinator.sources,
            'last_update_success': coordinator.last_update_success,
            'update_interval': (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
        },
        'zone_data': coordinator.data if coordinator.data else {},
    }
