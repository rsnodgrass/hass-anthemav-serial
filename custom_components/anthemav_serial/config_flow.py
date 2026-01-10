"""Config flow for Anthem AV Serial integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import voluptuous as vol

from .const import (
    CONF_MAX_VOLUME,
    CONF_SERIAL_NUMBER,
    CONF_SERIES,
    DEFAULT_MAX_VOLUME,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERIAL_NUMBER,
    DEFAULT_SERIES,
    DOMAIN,
    SUPPORTED_SERIES,
)

LOG = logging.getLogger(__name__)

# Human-readable labels for receiver series
SERIES_OPTIONS: list[SelectOptionDict] = [
    SelectOptionDict(value='d1', label='D1 Series'),
    SelectOptionDict(value='d2', label='D2 Series'),
    SelectOptionDict(value='d2v', label='D2v Series'),
    SelectOptionDict(value='avm20', label='AVM 20'),
    SelectOptionDict(value='avm30', label='AVM 30'),
    SelectOptionDict(value='avm50', label='AVM 50'),
    SelectOptionDict(value='mrx', label='MRX Series'),
]


class AnthemAVSerialConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Anthem AV Serial."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            port = user_input[CONF_PORT]
            series = user_input[CONF_SERIES]

            # validate series
            if series not in SUPPORTED_SERIES:
                errors['base'] = 'invalid_series'
            else:
                # use port as unique id (simpler than requiring serial number)
                unique_id = port

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = user_input.get(CONF_NAME) or f'Anthem {series.upper()}'

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_PORT: port,
                        CONF_SERIES: series,
                        CONF_SERIAL_NUMBER: DEFAULT_SERIAL_NUMBER,
                    },
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_MAX_VOLUME: DEFAULT_MAX_VOLUME,
                    },
                )

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORT): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_SERIES, default=DEFAULT_SERIES): SelectSelector(
                        SelectSelectorConfig(
                            options=SERIES_OPTIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return AnthemAVSerialOptionsFlow()


class AnthemAVSerialOptionsFlow(OptionsFlow):
    """Handle options flow for Anthem AV Serial."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title='', data=user_input)

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_max_volume = self.config_entry.options.get(
            CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME
        )

        return self.async_show_form(
            step_id='init',
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current_scan_interval
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=5,
                            max=300,
                            step=5,
                            mode=NumberSelectorMode.SLIDER,
                            unit_of_measurement='seconds',
                        )
                    ),
                    vol.Required(
                        CONF_MAX_VOLUME, default=current_max_volume
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0.0,
                            max=1.0,
                            step=0.05,
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
        )
