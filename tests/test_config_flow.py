"""Tests for the config flow."""

from unittest.mock import patch

from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gfm2.api import Gfm2ApiClientCommunicationError
from custom_components.gfm2.const import DOMAIN

from .conftest import TEST_IP, TEST_SERIAL


async def test_user_flow_creates_entry(hass, mock_api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Glasfaser-Modem 2 ({TEST_IP})"
    assert result["result"].unique_id == TEST_SERIAL
    assert result["result"].data == {CONF_IP_ADDRESS: TEST_IP}


async def test_duplicate_device_aborts(hass, mock_api):
    MockConfigEntry(
        domain=DOMAIN, data={CONF_IP_ADDRESS: TEST_IP}, unique_id=TEST_SERIAL
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_connection_error_shows_form_error(hass):
    with patch(
        "custom_components.gfm2.api.Gfm2ApiClient.async_get_status_data",
        side_effect=Gfm2ApiClientCommunicationError("boom"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}
