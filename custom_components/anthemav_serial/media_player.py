"""Media Player for Anthem A/V Receivers and Processors that support RS232 communication"""
import logging
import voluptuous as vol

from anthemav_serial import get_async_amp_controller
from anthemav_serial.config import DEVICE_CONFIG

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

CONF_SERIAL_CONFIG = "serial_config"

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
        vol.Optional(CONF_SERIAL_CONFIG): vol.Schema({}),
        vol.Required(CONF_SERIES, default="d2"): cv.string,  # FIXME: check if in SUPPORTED_ANTHEM_SERIES
        vol.Required(CONF_ZONES): vol.Schema({ZONE_IDS: ZONE_SCHEMA}),
        vol.Optional(CONF_SOURCES): vol.Schema({SOURCE_IDS: SOURCE_SCHEMA})
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
    """Setup the Anthem media player platform"""

    name = config.get(CONF_NAME)
    series = config.get(CONF_SERIES)
    serial_port = config.get(CONF_PORT)

    # allow configuration of the entire serial_init_args via YAML, instead of hardcoding baud
    #
    # E.g.:
    #  serial_config:
    #    baudrate: 9600
    serial_config = config.get(CONF_SERIAL_CONFIG)
    if not serial_config:
        serial_config = {}

#   FIXME: need to pass callback into amp controller to get notifications of changes
#    device = None
#    @callback
#    def async_anthemav_update_callback(message):
#        """Update notification that should be called whenever underlying data may have changed."""
#        LOG.debug("Update callback from Anthem AVR: %s", message)
#        hass.async_create_task(device.async_update_ha_state())

    LOG.info(f"Provisioning Anthem {series} media player at {serial_port} ({serial_config})")
    amp = await get_async_amp_controller(series, serial_port, hass.loop, serial_config_overrides=serial_config)
    if amp is None:
        LOG.error(f"Failed to connect to Anthem media player ({serial_port}; {serial_config})")
        return

    # FIXME: handle NO zones specified (e.g. load default for series)

    sources = config[CONF_SOURCES]

    # create a media_player device for each zone
    devices = []
    for zone, extra in config[CONF_ZONES].items():
        name = extra[CONF_NAME]
        LOG.info(f"Adding {series} zone {zone} - {name}")
        entity = AnthemAVSerial(amp, zone, name, sources)
        await entity.async_update()
        devices.append( entity )

    async_add_entities(devices)

class AnthemAVSerial(MediaPlayerDevice):
    """Entity reading values from Anthem AVR interface"""

    def __init__(self, amp, zone_id, name, sources):
        """Initialize Anthem media player zone"""
        super().__init__()
        self._amp = amp
        self._zone = zone_id
        self._name = name
        self._sources = sources
        self._zone_status = {}        

    @property
    def supported_features(self):
        """Return supported media player features"""
        return SUPPORTED_FEATURES_ANTHEM_SERIAL

    @property
    def should_poll(self):
        return True

    async def async_update(self):
        LOG.info(f"Updating amp status for zone {self._zone}")
        self._zone_status = await self._amp.zone_status(self._zone)

    @property
    def name(self):
        """Return name of device."""
        return self._name

    @property
    def state(self):
        """Return state of power on/off"""
        power = self._zone_status.get('power')
        if power is True:
            return STATE_ON
        elif power is False:
            return STATE_OFF
        LOG.warning(f"Could not determine power status for media player {self.name} from: {self._zone_status}")
        return None

    async def async_turn_on(self):
        await self._amp.set_power(self._zone, True)

    async def async_turn_off(self):
        await self._amp.set_power(self._zone, False)

    @property
    async def volume_level(self):
        """Return volume level from 0.0 to 1.0"""
        return self._zone_status.get('volume')

    async def async_set_volume_level(self, volume):
        """Set AVR volume (0.0 to 1.0)"""
        volume = min(volume,0.6) # FIXME hardcode to maximum 60% volume to protect system
        await self._amp.set_volume(volume)

    async def async_volume_up(self):
        await self._amp.volume_up(self._zone)

    async def async_volume_down(self):
        await self._amp.volume_down(self._zone)

    @property
    def is_volume_muted(self):
        """Return boolean reflecting mute state on device"""
        mute = self._zone_status.get('mute')
        if mute is True:
            return STATE_ON
        elif mute is False:
            return STATE_OFF
        LOG.warning(f"Could not determine power status for media player {self.name} from: {self._zone_status}")
        return None

    async def async_mute_volume(self, mute):
        await self._amp.set_mute(self._zone, mute)

    @property
    def source(self):
        """Return currently selected input""" # FIXME: by name?
        source = self._zone_status.get('source')
        return self._sources.get(source)

    @property
    def source_list(self):
        """Return all active, configured input source names"""
        return self._sources.keys()

    async def async_select_source(self, source):
        """Change AVR to the designated source (by name)"""
        # FIXME: cache the reverse map
        for source_id, source_name in self._sources:
            if source == source_name:
                await self._amp.set_source(self._zone, source_id)
                return
        LOG.warning(f"Could not change the media player {self.name} to source {source}")
