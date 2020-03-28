"""Media Player for Anthem A/V Receivers and Processors that support RS232 communication"""
import logging
import voluptuous as vol
from datetime import timedelta

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
from homeassistant.helpers.typing import HomeAssistantType
import homeassistant.helpers.config_validation as cv
# from homeassistant.util import Throttle

LOG = logging.getLogger(__name__)

DOMAIN = "anthemav_serial"

CONF_SERIAL_CONFIG = "serial_config"

CONF_SERIES = "series"
CONF_ZONES = "zones"
CONF_SOURCES = "sources"

SCAN_INTERVAL = timedelta(seconds=120)

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

async def async_setup_platform(hass: HomeAssistantType, config, async_add_entities, discovery_info=None):
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

 #   LOG.info(f"Provisioning Anthem {series} media player at {serial_port} (serial connection overrides {serial_config})")
 #   amp = await get_async_amp_controller(series, serial_port, hass.loop, serial_config_overrides=serial_config)
 #   if amp is None:
 #       LOG.error(f"Failed to connect to Anthem media player ({serial_port}; {serial_config})")
 #       return

    amp = None

    # FIXME: handle NO zones specified (e.g. load default for series)

    sources = config[CONF_SOURCES]

    # create a media_player device for each zone
    devices = []
    for zone, extra in config[CONF_ZONES].items():
        name = extra[CONF_NAME]
        LOG.info(f"Adding {series} zone {zone} - {name}")
        entity = AnthemAVSerial(amp, zone, name, sources)
#        await entity.async_update()
        devices.append( entity )

    LOG.info("Anthem AV setup complete")
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
    def supported_features(self) -> int:
        """Flags indicating supported media player features"""
        return SUPPORTED_FEATURES_ANTHEM_SERIAL

    @property
    def should_poll(self) -> bool:
        return False # FIXME

    async def async_added_to_hass(self):
         """Device added to hass."""
         LOG.debug("Called async_added_to_hass()")

    async def async_update(self):
        try:
            LOG.debug(f"Attempting update of '{self._name}' zone {self._zone} status")

            #status = await self._amp.zone_status(self._zone)
            status = None  # FIXME: testing

            if status and status != self._zone_status:
                self._zone_status = status
                LOG.info(f"Status for zone {self._zone} UPDATED! {self._zone_status}")
        except Exception as e:
            LOG.warning(f"Failure updating '{self._name}' zone {self._zone} status: {e}")

    @property
    def name(self) -> str:
        """Return name of device."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._name  # FIXME: need to determine unique id of unit

    @property
    def state(self) -> str:
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
    async def volume_level(self) -> float:
        """Return volume level (0.0 ... 1.0)"""
        volume = self._zone_status.get('volume')
        # if powered off, the device returns no volume level
        if volume is None:
            return None
        return volume

    async def async_set_volume_level(self, volume):
        """Set the volume (0.0 ... 1.0)"""
        volume = min(volume, 0.6) # FIXME hardcode to maximum 60% volume to protect system
        await self._amp.set_volume(volume)

    async def async_volume_up(self):
        await self._amp.volume_up(self._zone)

    async def async_volume_down(self):
        await self._amp.volume_down(self._zone)

    @property
    def is_volume_muted(self) -> bool:
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
        """Mute the volumn"""
        await self._amp.set_mute(self._zone, mute)

    @property
    def source(self) -> str:
        """Name of the current input source"""
        source = self._zone_status.get('source')
        if source is None:
            return None  # note if powered off, there is no source field
        return self._sources.get(source)

    @property
    def source_list(self) -> Sequence[str]:
        """Return all active, configured input source names"""
        return self._sources.keys()

    async def async_select_source(self, source):
        """Select input source."""
        # FIXME: cache the reverse map
        for source_id, source_name in self._sources:
            if source == source_name:
                await self._amp.set_source(self._zone, source_id)
                return
        LOG.warning(f"Could not change the media player {self.name} to source {source}")
