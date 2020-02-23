"""Media Player for Anthem A/V Receivers and Processors that support RS232 communication"""
import logging

from anthemav_serial import get_async_amp_controller
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
    ATTR_ENTITY_ID,
    CONF_NAME,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

LOG = logging.getLogger(__name__)

DOMAIN = "anthemav_serial"

CONF_SERIAL_PORT = "serial_port"
CONF_BAUD = "baudrate"

CONF_SERIES = "series"
CONF_ZONES = "zones"
CONF_SOURCES = "sources"

# from https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/blackbird/media_player.py
MEDIA_PLAYER_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.comp_entity_ids})

# FIXME: we can probably skip zones....
ZONE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})
ZONE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=3))   # valid zones: 1-3

SOURCE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})
SOURCE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=9)) # valid sources: 1-9

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_SERIES, default="d2"): cv.String,  # FIXME: check if in SUPPORTED_ANTHEM_SERIES
        vol.Required(CONF_ZONES): vol.Schema({ZONE_IDS: ZONE_SCHEMA}),
        vol.Optional(CONF_SOURCES): vol.Schema({SOURCE_IDS: SOURCE_SCHEMA}),
        vol.Optional(CONF_BAUD, default=9600): cv.int,
    }
)

SUPPORTED_FEATURES_ANTHEM_SERIAL = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE   
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up our socket to the AVR."""

    name = config.get(CONF_NAME)
    series = config.get(CONF_SERIES)
    serial_port = config.get(CONF_SERIAL_PORT)
    device = None

    LOG.info(f"Provisioning Anthem {series} receiver at {serial_port}")

    @callback
    def async_anthemav_update_callback(message):
        """Update notification that should be called whenever underlying data may have changed."""
        LOG.debug("Received update callback from Anthem AVR: %s", message)
        hass.async_create_task(device.async_update_ha_state())

    amp = await get_async_amp_controller(series, serial_port, hass.loop)
    if amp is None:
        LOG.error(f"Failed to connect to Anthem receiver ({serial_port}; baud={baud})")
        return

    # override default baudrate, if specified
    baud = config.get(CONF_BAUD)
    if baud:
        amp.set_baudrate(baud)

    # FIXME: handle NO zones specified (e.g. load default for series)

    # create a media_player device for each zone
    devices = []
    for zone_id, extra in config[CONF_ZONES].items():
        name = extra[CONF_NAME]
        LOG.info(f"Adding {series} zone {zone_id} - {name}")
        devices.append( AnthemAVSerial(amp, zone_id, name) )

    async_add_entities(devices)

class AnthemAVSerial(MediaPlayerDevice):
    """Entity reading values from Anthem AVR interface"""

    def __init__(self, amp, zone_id, name):
        """Initialize Anthem media player zone"""
        super().__init__()
        self._amp = amp
        self._zone_id = zone_id
        self._name = name

    def _lookup(self, propname, dval=None):
        return getattr(self.avr.protocol, propname, dval)

    @property
    def supported_features(self):
        """Flag media player features that are supported"""
        return SUPPORTED_FEATURES_ANTHEM_SERIAL

    @property
    def should_poll(self):
        """No polling needed."""
        return True # FIXME: make non-polling at some point

    @property
    def name(self):
        """Return name of device."""
        return self._name

    @property
    def state(self):
        """Return state of power on/off"""
        pwrstate = self._lookup("power")

        if pwrstate is True:
            return STATE_ON
        if pwrstate is False:
            return STATE_OFF
        return None

    @property
    def is_volume_muted(self):
        """Return boolean reflecting mute state on device"""
        return self._lookup("mute", False)

    @property
    def volume_level(self):
        """Return volume level from 0.0 to 1.0"""
        return self._lookup("volume_as_percentage", 0.0)

    def volume_up(self):
        """Volume up the media player"""
        #self._nad_receiver.main_volume("+")
        return

    def volume_down(self):
        """Volume down the media player"""
        # self._nad_receiver.main_volume("-")
        return
    
    @property
    def media_title(self):
        """Return current input name (closest we have to media title)"""
        return self._lookup("input_name", "No Source")

    @property
    def app_name(self):
        """Return details about current video and audio stream"""
        return (
            self._lookup("video_input_resolution_text", "")
            + " "
            + self._lookup("audio_input_name", "")
        )

    @property
    def source(self):
        """Return currently selected input"""
        return self._lookup("input_name", "Unknown")

    @property
    def source_list(self):
        """Return all active, configured inputs"""
        return self._lookup("input_list", ["Unknown"])

    async def async_select_source(self, source):
        """Change AVR to the designated source (by name)"""
        source_id = 1 # FIXME
        self._amp.set_source(zone_id, source_id)

        self._update_avr("input_name", source)

    async def async_turn_off(self):
        """Turn AVR power off"""
        self._amp.set_power(zone_id, False)

    async def async_turn_on(self):
        """Turn AVR power on"""
        self._amp.set_power(zone_id, True)

    async def async_set_volume_level(self, volume):
        """Set AVR volume (0.0 to 1.0)"""
#        self._update_avr("volume_as_percentage", volume)

    async def async_mute_volume(self, mute):
        """Engage AVR mute"""
        self._amp.set_mute(zone_id, True)

    def _update_avr(self, propname, value):
        """Update a property in the AVR"""
        LOG.info("Sending command to AVR: set %s to %s", propname, str(value))
        setattr(self.avr.protocol, propname, value)

    @property
    def dump_avrdata(self):
        """Return state of avr object for debugging forensics."""
        attrs = vars(self)
        return "dump_avrdata: " + ", ".join("%s: %s" % item for item in attrs.items())
