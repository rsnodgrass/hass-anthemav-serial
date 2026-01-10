"""Tests for Anthem AV Serial config flow."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.anthemav_serial.const import (
    CONF_MAX_VOLUME,
    CONF_SERIAL_NUMBER,
    CONF_SERIES,
    DEFAULT_MAX_VOLUME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SUPPORTED_SERIES,
)


async def test_form(hass: HomeAssistant) -> None:
    """Test config flow shows the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'user'
    assert result['errors'] == {}


async def test_form_valid_input(hass: HomeAssistant) -> None:
    """Test config flow with valid input creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    assert result['type'] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_PORT: '/dev/ttyUSB0',
            CONF_SERIES: 'd2v',
            CONF_NAME: 'My Anthem',
            CONF_SERIAL_NUMBER: '123456',
        },
    )

    assert result2['type'] == FlowResultType.CREATE_ENTRY
    assert result2['title'] == 'My Anthem'
    assert result2['data'] == {
        CONF_PORT: '/dev/ttyUSB0',
        CONF_SERIES: 'd2v',
        CONF_SERIAL_NUMBER: '123456',
    }
    assert result2['options'] == {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_MAX_VOLUME: DEFAULT_MAX_VOLUME,
    }


async def test_form_default_name(hass: HomeAssistant) -> None:
    """Test config flow uses series as default title when no name provided."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_PORT: '/dev/ttyUSB1',
            CONF_SERIES: 'mrx',
            CONF_NAME: '',
            CONF_SERIAL_NUMBER: '654321',
        },
    )

    assert result2['type'] == FlowResultType.CREATE_ENTRY
    assert result2['title'] == 'Anthem MRX'


async def test_form_invalid_series(hass: HomeAssistant) -> None:
    """Test config flow with invalid series shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    # patch SUPPORTED_SERIES to simulate invalid series
    with patch(
        'custom_components.anthemav_serial.config_flow.SUPPORTED_SERIES',
        ['d2v', 'mrx'],
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_PORT: '/dev/ttyUSB0',
                CONF_SERIES: 'invalid_series',
                CONF_NAME: 'Test',
                CONF_SERIAL_NUMBER: '123456',
            },
        )

    assert result2['type'] == FlowResultType.FORM
    assert result2['errors'] == {'base': 'invalid_series'}


async def test_form_duplicate_unique_id(hass: HomeAssistant) -> None:
    """Test config flow aborts when unique ID is already configured."""
    # create an initial entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_PORT: '/dev/ttyUSB0',
            CONF_SERIES: 'd2v',
            CONF_NAME: 'First Anthem',
            CONF_SERIAL_NUMBER: '123456',
        },
    )

    # try to create duplicate
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2['flow_id'],
        {
            CONF_PORT: '/dev/ttyUSB0',
            CONF_SERIES: 'd2v',
            CONF_NAME: 'Second Anthem',
            CONF_SERIAL_NUMBER: '123456',
        },
    )

    assert result3['type'] == FlowResultType.ABORT
    assert result3['reason'] == 'already_configured'


@pytest.mark.parametrize('series', SUPPORTED_SERIES)
async def test_form_all_supported_series(hass: HomeAssistant, series: str) -> None:
    """Test config flow accepts all supported series."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_PORT: f'/dev/ttyUSB_{series}',
            CONF_SERIES: series,
            CONF_NAME: f'Anthem {series}',
            CONF_SERIAL_NUMBER: f'{series}_123',
        },
    )

    assert result2['type'] == FlowResultType.CREATE_ENTRY
    assert result2['data'][CONF_SERIES] == series
