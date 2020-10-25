"""Media Player for Anthem A/V Receivers and Processors that support RS232 communication"""

import logging
import voluptuous as vol
from datetime import timedelta

from anthemav_serial import get_async_amp_controller
from anthemav_serial.config import DEVICE_CONFIG
#from anthemav_serial.const import MUTE_KEY, VOLUME_KEY, POWER_KEY, SOURCE_KEY, ZONE_KEY

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

from .const import DOMAIN, CONF_SERIAL_CONFIG, CONF_SERIAL_NUMBER, CONF_SERIES, CONF_ZONES, CONF_SOURCES

LOG = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

# from https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/blackbird/media_player.py
MEDIA_PLAYER_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.comp_entity_ids})

CONF_MAX_VOLUME = 'max_volume'
DEFAULT_MAX_VOLUME = 0.6
MAX_VOLUME_SCHEMA = vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0))

ZONE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_MAX_VOLUME, default=DEFAULT_MAX_VOLUME): MAX_VOLUME_SCHEMA,
})
ZONE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=3))   # valid zones: 1-3

# if no zones are specified default to a single main zone for the amp
DEFAULT_ZONE_CONFIG = {
    1: {
        CONF_NAME: "Main", # FIXME: translation
        CONF_MAX_VOLUME: DEFAULT_MAX_VOLUME
       }  
}

SOURCE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})
SOURCE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=9)) # valid sources: 1-9

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_PORT): cv.string,
    vol.Optional(CONF_SERIAL_CONFIG, default={}): vol.Schema({}),
    vol.Required(CONF_SERIES, default="d2v"): cv.string,
    vol.Optional(CONF_ZONES, default=DEFAULT_ZONE_CONFIG): vol.Schema({ZONE_IDS: ZONE_SCHEMA}),
    vol.Optional(CONF_SOURCES): vol.Schema({SOURCE_IDS: SOURCE_SCHEMA}),
    vol.Optional(CONF_SERIAL_NUMBER, default='000000'): cv.string
})

SUPPORTED_FEATURES_ANTHEM_SERIAL = (
    SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_SELECT_SOURCE   
)

async def async_setup_platform(hass: HomeAssistantType, config, async_add_entities, discovery_info=None):
    """Setup the Anthem media player platform"""

    series = config.get(CONF_SERIES)
    if not series in DEVICE_CONFIG:
        LOG.error("Invalid series '{series}' specified, no protocol provided by anthemav_serial")
        return

    # allow configuration of the entire serial_init_args via YAML, instead of hardcoding baud
    #
    # E.g.:
    #  serial_config:
    #    baudrate: 9600
    serial_port = config.get(CONF_PORT)
    serial_overrides = config.get(CONF_SERIAL_CONFIG)

    LOG.info(f"Provisioning Anthem {series} media player at {serial_port} (overrides={serial_overrides})")

    # FIXME: This is what blocks the event loop (later accesses of amp)
    amp = await get_async_amp_controller(series, serial_port, hass.loop, serial_config_overrides=serial_overrides)
    #if amp is None:
    #    LOG.error(f"Failed to connect to Anthem media player ({serial_port}; {serial_overrides})")
    #    return
    #amp = None

    # if no sources are configured by user, default to ALL the sources for the specified amp series
    sources = config.get(CONF_SOURCES, DEVICE_CONFIG[series].get(CONF_SOURCES))

    flattened_sources = {}
    for zone_id, data in sources.items():
        flattened_sources[zone_id] = data[CONF_NAME]
    LOG.info(f"Configuring {series} sources: {flattened_sources}")

    zones = config[CONF_ZONES]

    # TODO: for Anthems with V2 protocol, default to serial number from IDN? query
    serial_number = config[CONF_SERIAL_NUMBER]

    # create a media_player for each configured zone
    entities = []
    for zone, zone_config in zones.items():
        name = zone_config.get(CONF_NAME, f"Zone {zone}")

        LOG.info(f"Adding {series} zone {zone} ({name})")
        entity = AnthemAVSerial(zone_config, amp, serial_number, zone, name, flattened_sources)
        entities.append( entity )

        # trigger an immediate update
        #await entity.async_update()

    LOG.warning(f"WHAT entities={entities} / {async_add_entities}")
    if entities:
        await async_add_entities(entities)
    LOG.info(f"Setup of {series} (serial number={serial_number}) complete: {flattened_sources}: {entities}")

class AnthemAVSerial(MediaPlayerEntity):
    """Entity reading values from Anthem AVR interface"""

    def __init__(self, config, amp, serial_number, zone, name, sources):
        """Initialize Anthem media player zone"""
        self._config = config
        self._amp = amp
        self._zone = zone
        self._name = name
        self._sources = sources

        self._unique_id = f"{DOMAIN}_{serial_number}_{zone}"

        LOG.info(f"Setting up {name} one {zone}: {sources} - {self.entity_id} / unique = {self.unique_id}")
        self._source_names_to_id = {}
        for zone_id, name in self._sources.items():
            self._source_names_to_id[name] = zone_id

        self._zone_status = {}
        self._attr = {
            CONF_MAX_VOLUME: float(self._config.get(CONF_MAX_VOLUME))
        }

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
            status = None
            #status = await self._amp.zone_status(self._zone)
            if status and status != self._zone_status:
                self._zone_status = status
                LOG.info(f"Status for zone {self._zone} UPDATED! {self._zone_status}")
        except Exception as e:
            LOG.warning(f"Failed updating '{self._name}' (zone {self._zone}) status: {e}")

    @property
    def name(self):
        """Return name of device."""
        return self._name

    @property
    def state(self):
        """Return state of power on/off"""
        power = self._zone_status.get('power')
        LOG.debug(f"Found power '{power}' state for '{self._name}' zone {self._zone} status")
        if power == True:
            return STATE_ON
        elif power == False:
            return STATE_OFF
        LOG.warning(f"Missing {self.name} zone {self._zone} power status: {self._zone_status}")
        return None

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
            return None
        return float(volume)

    async def async_set_volume_level(self, volume):
        """Set the volume (0.0 ... 1.0)"""

        # enforce the max_volume level setting
        max_volume = float(self._config.get(CONF_MAX_VOLUME))
        if volume > max_volume:
            LOG.warning("Volume setting {volume} is higher than the {self._name} (zone {self._zone}) max_volume {max_volume}, limiting it to {max_volume}")
            volume = max_volume
        else:
            LOG.info(f"Setting volume for {self._name} (zone {self._zone}) to {volume}")

        await self._amp.set_volume(volume)

    async def async_volume_up(self):
        LOG.info(f"Increasing volume for {self._name} (zone {self._zone})")
        # FIXME: need to ensure this also limits to the max_volume setting
        await self._amp.volume_up(self._zone)
        return

    async def async_volume_down(self):
        LOG.info(f"Decreasing volume for {self._name} (zone {self._zone})")
        await self._amp.volume_down(self._zone)
        return

    @property
    def is_volume_muted(self):
        """Return boolean reflecting mute state on device"""
        mute = self._zone_status.get('mute')
        if mute is None:
            return STATE_ON  # note if powered off, the amp is "muted"
            # FIXME: should this be None or STATE_OFF?

        if mute == True:
            return STATE_ON
        elif mute == False:
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
            return None # NOTE: if powered off, there is no source

        name = self._sources.get(source_id)
        if not name:
            # dynamically add a source, if the current source wasn't configured by the user
            # FIXME: use translations!
            name = f"Source {source_id}"
            self._sources[source_id] = name
            self._source_names_to_id[name] = source_id
        return name

    @property
    def source_list(self):
        """Return all active, configured input source names"""
        return self._source_names_to_id.keys()
        return None

    async def async_select_source(self, source):
        """Select input source."""
        for source_name, source_id in self._source_names_to_id:
            if source_name == source:
                await self._amp.set_source(self._zone, source_id)
                return
        LOG.warning(f"Cannot change media player {self.name} to source {source}, source not found!")
