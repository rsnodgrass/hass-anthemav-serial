"""Media Player for Anthem A/V Receivers and Processors that support RS232 communication"""
import logging
import voluptuous as vol
from datetime import timedelta

from anthemav_serial import get_async_amp_controller
from anthemav_serial.config import DEVICE_CONFIG

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
    SUPPORT_SELECT_SOURCE
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    CONF_PORT,
    STATE_OFF,
    STATE_ON
)
from homeassistant.core import callback
from homeassistant.helpers.typing import HomeAssistantType
import homeassistant.helpers.config_validation as cv

from . import DOMAIN, CONF_SERIAL_CONFIG

LOG = logging.getLogger(__name__)

CONF_SERIES = "series"
CONF_ZONES = "zones"
CONF_SOURCES = "sources"

SCAN_INTERVAL = timedelta(seconds=10)

# from https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/blackbird/media_player.py
MEDIA_PLAYER_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.comp_entity_ids})

ZONE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})
ZONE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=3))   # valid zones: 1-3

# only create a single main zone for the amp, if none are specified
DEFAULT_ZONES = {
    1: { "name": "Main" }
}

SOURCE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})
SOURCE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=9)) # valid sources: 1-9

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Optional(CONF_SERIAL_CONFIG): vol.Schema({}),
        vol.Required(CONF_SERIES, default="d2v"): cv.string,
        vol.Required(CONF_ZONES): vol.Schema({ZONE_IDS: ZONE_SCHEMA}),
        vol.Optional(CONF_SOURCES): vol.Schema({SOURCE_IDS: SOURCE_SCHEMA})
    }
)

SUPPORTED_FEATURES_ANTHEM_SERIAL = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
#    | SUPPORT_VOLUME_STEP
#    | SUPPORT_VOLUME_MUTE
#    | SUPPORT_TURN_ON
#    | SUPPORT_TURN_OFF
#    | SUPPORT_SELECT_SOURCE   
)

async def async_setup_platform(hass: HomeAssistantType, config, async_add_entities, discovery_info=None):
    """Setup the Anthem media player platform"""

    series = config.get(CONF_SERIES)
    if not series in DEVICE_CONFIG:
        LOG.error("Invalid series '{series}' specified, no such config in anthemav_serial")
        return

    # allow configuration of the entire serial_init_args via YAML, instead of hardcoding baud
    #
    # E.g.:
    #  serial_config:
    #    baudrate: 9600
    serial_port = config.get(CONF_PORT)
    serial_overrides = config.get(CONF_SERIAL_CONFIG)
    if not serial_overrides:
        serial_overrides = {}

    LOG.info(f"Provisioning Anthem {series} media player at {serial_port} (serial connection overrides {serial_overrides})")
    amp = await get_async_amp_controller(series, serial_port, hass.loop, serial_config_overrides=serial_overrides)
    if amp is None:
        LOG.error(f"Failed to connect to Anthem media player ({serial_port}; {serial_overrides})")
        return

    # check if amp is connected (if not, ignore this amp?)
    LOG.warning("Checking amp status")
    result = await amp.zone_status(1)
    LOG.warning(f"Amp status: {result}")

    # if no sources are defined, then populate with ALL the sources for the specified amp series
    sources = config[CONF_SOURCES]
    series_sources = DEVICE_CONFIG[series].get('sources')
    # FIXME: validate any configured source ids are actually in the series_sources list
    if sources is None:
        sources = series_sources

    flattened_sources = {}
    for zone_id, data in sources.items():
        flattened_sources[zone_id] = data['name']
    LOG.info(f"{series} sources: {flattened_sources}")

    # if no zones are defined, use the defaults (only single Main zone)
    zones = config[CONF_ZONES]
    if zones is None:
        zones = DEFAULT_ZONES

    # create a separate media_player for each configured zone
    entities = []
    for zone, extra in zones.items():
        name = extra[CONF_NAME]
        LOG.info(f"Adding {series} zone {zone} ({name})")
        entity = AnthemAVSerial(amp, zone, name, flattened_sources)
        await entity.async_update()
        entities.append( entity )

    async_add_entities(entities)
    LOG.info(f"Setup of Anthem {series} complete")

class AnthemAVSerial(MediaPlayerEntity):
    """Entity reading values from Anthem AVR interface"""

    def __init__(self, amp, zone, name, sources):
        """Initialize Anthem media player zone"""
        self._amp = amp
        self._zone = zone
        self._name = name
        self._sources = sources

        self._unique_id = "{DOMAIN}_{zone}"

        LOG.info(f"Setting up {name} one {zone}: {sources} - {self.entity_id} / unique = {self.unique_id}")
        self._source_names_to_id = {}
        for zone_id, name in self._sources.items():
            self._source_names_to_id[name] = zone_id

        self._zone_status = {}

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._unique_id

    @property
    def supported_features(self):
        """Flags indicating supported media player features"""
        return SUPPORTED_FEATURES_ANTHEM_SERIAL

    @property
    def should_poll(self):
        return True

    async def async_update(self):
        try:
            status = await self._amp.zone_status(self._zone)
            if status and status != self._zone_status:
                self._zone_status = status
                LOG.info(f"Status for zone {self._zone} UPDATED! {self._zone_status}")
        except Exception as e:
            LOG.warning(f"Failed updating '{self._name}' zone {self._zone} status: {e}")

    @property
    def name(self):
        """Return name of device."""
        return self._name

    @property
    def state(self):
        """Return state of power on/off"""
        LOG.debug(f"Power state of '{self._name}' zone {self._zone} status")
        power = self._zone_status.get('power')
        LOG.debug(f"Found state of '{self._name}' zone {self._zone} status: power {power}")
        if power is True:
            return STATE_ON
        elif power is False:
            return STATE_OFF
        LOG.warning(f"Missing {self.name}/zone {self._zone} power status: {self._zone_status}")
        return STATE_OFF

    async def async_turn_on(self):
        LOG.info(f"Turning on amp {self._name} zone {self._zone}")
        await self._amp.set_power(self._zone, True)
        return

    async def async_turn_off(self):
        LOG.info(f"Turning off amp {self._name} zone {self._zone}")
        await self._amp.set_power(self._zone, False)
        return

    @property
    async def volume_level(self):
        """Return volume level (0.0 ... 1.0)"""
        volume = self._zone_status.get('volume')
        # if powered off, the device returns no volume level
        if volume is None:
            return 0.0 # FIXME: or None?
        return volume

    async def async_set_volume_level(self, volume):
        """Set the volume (0.0 ... 1.0)"""
        volume = min(volume, 0.6) # FIXME hardcode to maximum 60% volume to protect system
        LOG.info(f"Setting volume for amp {self._name} zone {self._zone} to {volume}")
        #await self._amp.set_volume(volume)

    async def async_volume_up(self):
        LOG.info(f"Increasing volume for amp {self._name} zone {self._zone}")
        #await self._amp.volume_up(self._zone)
        return

    async def async_volume_down(self):
        LOG.info(f"Decreasing volume for amp {self._name} zone {self._zone}")
        #await self._amp.volume_down(self._zone)
        return

    @property
    def is_volume_muted(self):
        """Return boolean reflecting mute state on device"""
        mute = self._zone_status.get('mute')
        if mute is None:
            return STATE_OFF  # note if powered off, there is no mute field
            # FIXME: should this be None or STATE_OFF?

        if mute is True:
            return STATE_ON
        elif mute is False:
            return STATE_OFF

    async def async_mute_volume(self, mute):
        """Mute the volume"""
        await self._amp.set_mute(self._zone, mute)
        return

    @property
    def source(self):
        """Name of the current input source"""
        source_id = self._zone_status.get('source')
        if source_id is None:
            return None  # note if powered off, there is no source field

        name = self._sources.get(source_id)
        if not name:
            # dynamically add, if this souce hasn't been configured
            name = f"Source {source_id}"
            self._sources[source_id] = name
            self._source_names_to_id[name] = source_id
        return name

   # @property
   # def source_list(self):
   #     """Return all active, configured input source names"""
   #     LOG.info(f"Return sources {self._source_names_to_id.keys()}")
   #     return None

    async def async_select_source(self, source):
        """Select input source."""
        # FIXME: cache the reverse map
        for source_name, source_id in self._source_names_to_id:
            if source == source_name:
                await self._amp.set_source(self._zone, source_id)
                return
        LOG.warning(f"Could not change the media player {self.name} to source {source}")
