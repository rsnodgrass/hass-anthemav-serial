"""Support for Anthem A/V Receivers and Processors that support RS232 communication"""
import logging

import anthemav_serial
import voluptuous as vol

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerDevice
from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP
)
from homeassistant.const import (
    CONF_NAME,
    EVENT_HOMEASSISTANT_STOP,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

LOG = logging.getLogger(__name__)

DOMAIN = "anthemav_serial"

SUPPORT_ANTHEMAV = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE   
)

CONF_SERIAL_PORT = 'serial_port'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_NAME): cv.string
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up our socket to the AVR."""

    tty = config.get(CONF_SERIAL_PORT)
    name = config.get(CONF_NAME)
    device = None

    LOG.info(f"Provisioning Anthem receiver/amp at {serial_port}")

    @callback
    def async_anthemav_update_callback(message):
        """Receive notification from transport that new data exists."""
        LOG.debug("Received update callback from AVR: %s", message)
        hass.async_create_task(device.async_update_ha_state())

    conn = await anthemav.Connection.create(
        host=host, port=port, update_callback=async_anthemav_update_callback
    )
    device = AnthemAVR(conn, name)

#    LOG.debug("dump_devicedata: %s", device.dump_avrdata)
#    LOG.debug("dump_conndata: %s", avr.dump_conndata)

#    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, device.avr.close)
    async_add_entities([device])


class AnthemAVR(MediaPlayerDevice):
    """Entity reading values from Anthem AVR interface."""

    def __init__(self, avr, name):
        """Initialize entity with transport."""
        super().__init__()
        self.avr = avr
        self._name = name

    def _lookup(self, propname, dval=None):
        return getattr(self.avr.protocol, propname, dval)

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_ANTHEMAV

    @property
    def should_poll(self):
        """No polling needed."""
        return False # FIXME: True

    @property
    def name(self):
        """Return name of device."""
        return self._name or self._lookup("model")

    @property
    def state(self):
        """Return state of power on/off."""
        pwrstate = self._lookup("power")

        if pwrstate is True:
            return STATE_ON
        if pwrstate is False:
            return STATE_OFF
        return None

    @property
    def is_volume_muted(self):
        """Return boolean reflecting mute state on device."""
        return self._lookup("mute", False)

    @property
    def volume_level(self):
        """Return volume level from 0 to 1."""
        return self._lookup("volume_as_percentage", 0.0)

    @property
    def media_title(self):
        """Return current input name (closest we have to media title)."""
        return self._lookup("input_name", "No Source")

    @property
    def app_name(self):
        """Return details about current video and audio stream."""
        return (
            self._lookup("video_input_resolution_text", "")
            + " "
            + self._lookup("audio_input_name", "")
        )

    @property
    def source(self):
        """Return currently selected input."""
        return self._lookup("input_name", "Unknown")

    @property
    def source_list(self):
        """Return all active, configured inputs."""
        return self._lookup("input_list", ["Unknown"])

    async def async_select_source(self, source):
        """Change AVR to the designated source (by name)."""
        self._update_avr("input_name", source)

    async def async_turn_off(self):
        """Turn AVR power off."""
        self._update_avr("power", False)

    async def async_turn_on(self):
        """Turn AVR power on."""
        self._update_avr("power", True)

    async def async_set_volume_level(self, volume):
        """Set AVR volume (0 to 1)."""
        self._update_avr("volume_as_percentage", volume)

    async def async_mute_volume(self, mute):
        """Engage AVR mute."""
        self._update_avr("mute", mute)

    def _update_avr(self, propname, value):
        """Update a property in the AVR."""
        LOG.info("Sending command to AVR: set %s to %s", propname, str(value))
        setattr(self.avr.protocol, propname, value)

    @property
    def dump_avrdata(self):
        """Return state of avr object for debugging forensics."""
        attrs = vars(self)
        return "dump_avrdata: " + ", ".join("%s: %s" % item for item in attrs.items())
