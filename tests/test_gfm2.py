"""Unit tests for the Gfm2 data layer (no Home Assistant instance needed)."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.gfm2.gfm2 import Gfm2

from .conftest import load_json_fixture

BERLIN = ZoneInfo("Europe/Berlin")


class StubApi:
    """Minimal stand-in for Gfm2ApiClient."""

    def __init__(self, status=None, firmware=None, reboot=None):
        self._status = status if status is not None else []
        self._firmware = firmware if firmware is not None else []
        self._reboot = reboot if reboot is not None else []

    async def async_get_status_data(self):
        return self._status

    async def async_get_firmware_data(self):
        return self._firmware

    async def async_get_reboot_data(self):
        return self._reboot


async def test_reboot_timestamp_uses_configured_time_zone():
    device = Gfm2(StubApi(reboot=load_json_fixture("reboot.json")), time_zone=BERLIN)
    data = await device.get_reboot_data()
    assert data["custom_last_reboot"] == datetime(2025, 12, 3, 22, 48, tzinfo=BERLIN)
    assert data["custom_last_reboot"].utcoffset() == timedelta(hours=1)  # CET


async def test_firmware_timestamp_uses_configured_time_zone():
    device = Gfm2(
        StubApi(firmware=load_json_fixture("firmware.json")), time_zone=BERLIN
    )
    data = await device.get_firmware_data()
    assert data["firmware_firmware_date"] == datetime(
        2020, 9, 21, 10, 4, 48, tzinfo=BERLIN
    )
    assert data["firmware_firmware_date"].utcoffset() == timedelta(hours=2)  # CEST


async def test_incomplete_status_does_not_raise():
    device = Gfm2(
        StubApi(status=load_json_fixture("status_incomplete.json")), time_zone=BERLIN
    )
    data = await device.get_status_data()
    assert data["custom_fiber_connection"] is False
    assert data["status_hardware_state"] is False  # kein Befund ohne Daten
    assert data.get("status_txpower") is None


async def test_malformed_payload_does_not_raise():
    device = Gfm2(
        StubApi(status={"unexpected": "shape"}, firmware="no list", reboot=None),
        time_zone=BERLIN,
    )
    status = await device.get_status_data()
    firmware = await device.get_firmware_data()
    reboot = await device.get_reboot_data()
    assert status["custom_fiber_connection"] is False
    assert firmware["firmware_firmware_date"] is None
    assert reboot["custom_last_reboot"] is None


async def test_unparseable_power_is_not_reported_as_a_fiber_connection():
    """A non-numeric power value other than "--" must not count as a live link."""
    status = [
        {"vartype": "value", "varid": "txpower", "varvalue": ""},
        {"vartype": "value", "varid": "rxpower", "varvalue": "n/a"},
    ]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    data = await device.get_status_data()
    assert data["custom_fiber_connection"] is False
    assert data["status_txpower"] is None
    assert data["status_rxpower"] is None


async def test_non_finite_power_is_treated_as_unknown():
    """NaN and infinity parse as floats but must never reach a sensor state."""
    status = [
        {"vartype": "value", "varid": "txpower", "varvalue": "NaN"},
        {"vartype": "value", "varid": "rxpower", "varvalue": "-20"},
    ]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    data = await device.get_status_data()
    assert data["custom_fiber_connection"] is False
    assert data["status_txpower"] is None
    assert data["status_rxpower"] == -20.0


async def test_hardware_state_zero_is_fault():
    device = Gfm2(
        StubApi(status=load_json_fixture("status_hw_fault.json")), time_zone=BERLIN
    )
    data = await device.get_status_data()
    assert data["status_hardware_state"] is True  # True == Problem


async def test_hardware_state_unexpected_value_is_ok():
    status = [{"vartype": "value", "varid": "hardware_state", "varvalue": "2"}]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    data = await device.get_status_data()
    assert data["status_hardware_state"] is False


async def test_properties_return_none_when_data_missing():
    device = Gfm2(StubApi(), time_zone=BERLIN)
    await device.get_all_data()
    assert device.serial_number is None
    assert device.device_name is None
