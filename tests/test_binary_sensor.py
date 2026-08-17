"""Tests for binary sensor states."""

from .conftest import load_json_fixture


async def _setup(hass, config_entry):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_hardware_status_ok(hass, config_entry, mock_api):
    await _setup(hass, config_entry)
    assert (
        hass.states.get("binary_sensor.glasfaser_modem_2_hardware_status").state
        == "off"
    )
    assert (
        hass.states.get("binary_sensor.glasfaser_modem_2_fiber_connection").state
        == "on"
    )


async def test_hardware_fault(hass, config_entry, mock_api):
    mock_api["status"].return_value = load_json_fixture("status_hw_fault.json")
    await _setup(hass, config_entry)
    assert (
        hass.states.get("binary_sensor.glasfaser_modem_2_hardware_status").state == "on"
    )


async def test_no_link_turns_fiber_connection_off(hass, config_entry, mock_api):
    mock_api["status"].return_value = load_json_fixture("status_no_link_real.json")
    await _setup(hass, config_entry)
    assert (
        hass.states.get("binary_sensor.glasfaser_modem_2_fiber_connection").state
        == "off"
    )
