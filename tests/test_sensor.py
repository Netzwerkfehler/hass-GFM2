"""Tests for sensor states."""

from datetime import UTC, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import STATE_UNKNOWN, UnitOfDataRate
from homeassistant.util import dt as dt_util

from .conftest import load_json_fixture


async def test_last_reboot_is_read_as_device_local_time(hass, config_entry, mock_api):
    """
    The device reports local time, so it must not be parsed as UTC.

    The fixture reports "03.12.2025 22:48". In Europe/Berlin that is UTC+1 in
    winter, so the correct instant is 21:48 UTC. Parsing it as UTC instead puts
    the timestamp one hour into the future.

    Home Assistant renders timestamp states in UTC, so this compares the
    instant rather than its notation.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.glasfaser_modem_2_last_reboot")
    assert dt_util.parse_datetime(state.state) == datetime(
        2025, 12, 3, 21, 48, tzinfo=UTC
    )


async def test_link_status_zero_reports_unknown(hass, config_entry, mock_api):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.glasfaser_modem_2_lan_link")
    assert state.state == STATE_UNKNOWN
    assert state.attributes["unit_of_measurement"] == UnitOfDataRate.MEGABITS_PER_SECOND
    assert state.attributes["device_class"] == SensorDeviceClass.DATA_RATE
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT


async def test_link_status_1000_reports_data_rate(hass, config_entry, mock_api):
    mock_api["status"].return_value = load_json_fixture("status_no_link_real.json")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.glasfaser_modem_2_lan_link")
    assert state.state == "1000"
    assert state.attributes["unit_of_measurement"] == UnitOfDataRate.MEGABITS_PER_SECOND
    assert state.attributes["device_class"] == SensorDeviceClass.DATA_RATE
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
