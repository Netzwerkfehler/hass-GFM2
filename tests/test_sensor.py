"""Tests for sensor states."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import STATE_UNKNOWN, UnitOfDataRate
from homeassistant.util import dt as dt_util

from custom_components.gfm2.gfm2 import Gfm2

from .conftest import load_json_fixture
from .test_gfm2 import StubApi


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


async def test_sensor_values_from_recorded_fixture(hass, config_entry, mock_api):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        hass.states.get("sensor.glasfaser_modem_2_lan_packets_sent").state
        == "1875424524"
    )
    assert hass.states.get("sensor.glasfaser_modem_2_pon_tx_power").state == "2.39"
    assert hass.states.get("sensor.glasfaser_modem_2_pon_rx_power").state == "-16.13"
    assert hass.states.get("sensor.glasfaser_modem_2_ui_version").state == "2.18.161"


async def test_numeric_values_are_numbers():
    """
    Verify that the data layer returns numbers for numeric sensors.

    This guards native Home Assistant statistics against string values.
    """
    device = Gfm2(
        StubApi(status=load_json_fixture("status_full.json")),
        time_zone=ZoneInfo("Europe/Berlin"),
    )
    data = await device.get_status_data()
    assert data["status_txpackets"] == 1875424524
    assert isinstance(data["status_txpackets"], int)
    assert data["status_txpower"] == 2.39
    assert isinstance(data["status_txpower"], float)
    assert data["status_rxbip_crc"] == 0
