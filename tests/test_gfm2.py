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
    assert data["custom_last_reboot"] == datetime(2026, 7, 1, 4, 30, tzinfo=BERLIN)
    assert data["custom_last_reboot"].utcoffset() == timedelta(hours=2)  # CEST


async def test_firmware_timestamp_uses_configured_time_zone():
    device = Gfm2(
        StubApi(firmware=load_json_fixture("firmware.json")), time_zone=BERLIN
    )
    data = await device.get_firmware_data()
    assert data["firmware_firmware_date"] == datetime(
        2025, 11, 20, 8, 15, 30, tzinfo=BERLIN
    )
    assert data["firmware_firmware_date"].utcoffset() == timedelta(hours=1)  # CET
