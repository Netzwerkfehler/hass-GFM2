"""Unit tests for the Gfm2 data layer (no Home Assistant instance needed)."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.gfm2.api import Gfm2ApiClientCommunicationError
from custom_components.gfm2.gfm2 import Gfm2

from .conftest import load_extended_fixture, load_json_fixture

BERLIN = ZoneInfo("Europe/Berlin")
UTC = ZoneInfo("UTC")


class StubApi:
    """Minimal stand-in for Gfm2ApiClient."""

    def __init__(self, status=None, firmware=None, reboot=None, extended=None):
        self._status = status if status is not None else []
        self._firmware = firmware if firmware is not None else []
        self._reboot = reboot if reboot is not None else []
        # Eine Funktion von Seitenname auf Antwort; ohne sie liefert der Stub
        # leere Seiten wie ein Modem, das nichts zu melden hat.
        self._extended = extended

    async def async_get_extended_data(self, page):
        return self._extended(page) if self._extended is not None else []

    async def async_get_status_data(self):
        return self._status

    async def async_get_firmware_data(self):
        return self._firmware

    async def async_get_reboot_data(self):
        return self._reboot


async def test_reboot_timestamp_uses_configured_time_zone():
    device = Gfm2(StubApi(reboot=load_json_fixture("reboot.json")), time_zone=BERLIN)
    data = await device.get_reboot_data()
    assert data["custom_last_reboot"] == datetime(2025, 12, 3, 22, 48, tzinfo=UTC)
    assert data["custom_last_reboot"].utcoffset() == timedelta(hours=0)  # UTC


async def test_reboot_timestamp_is_none_when_never_rebooted():
    # Aufzeichnung eines Geraets, das nie ueber den Reboot-Button neu gestartet
    # wurde: beide Felder sind leer, nicht etwa abwesend.
    device = Gfm2(
        StubApi(reboot=load_json_fixture("reboot_never.json")), time_zone=BERLIN
    )
    data = await device.get_reboot_data()
    assert data["reboot_reboot_date"] == ""
    assert data["reboot_reboot_time"] == ""
    assert data["custom_last_reboot"] is None


async def test_firmware_timestamp_uses_configured_time_zone():
    device = Gfm2(
        StubApi(firmware=load_json_fixture("firmware.json")), time_zone=BERLIN
    )
    data = await device.get_firmware_data()
    assert data["firmware_firmware_date"] == datetime(
        2020, 9, 21, 10, 4, 48, tzinfo=UTC
    )
    assert data["firmware_firmware_date"].utcoffset() == timedelta(hours=0)  # UTC


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


async def test_non_string_serial_number_is_refused():
    # Die Seriennummer wird dauerhaft als unique_id uebernommen. Ein Ueberrest
    # einer kaputten Antwort darf dort nicht als Text landen.
    status = [
        {"vartype": "value", "varid": "serial_number", "varvalue": {"broken": True}}
    ]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    await device.get_all_data()
    assert device.serial_number is None


async def test_blank_serial_number_is_refused():
    status = [{"vartype": "value", "varid": "serial_number", "varvalue": "   "}]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    await device.get_all_data()
    assert device.serial_number is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Werte aus Issue #142: der Zaehler laeuft weiter, wird aber signed
        # ausgegeben, sobald er 2**31 ueberschreitet.
        ("-2119064655", 2175902641),
        ("-1", 4294967295),
        ("-2147483648", 2147483648),
        ("2147483647", 2147483647),
        ("0", 0),
    ],
)
@pytest.mark.parametrize("varid", ["txpackets", "rxpackets", "rxdrop_packets"])
async def test_packet_counters_are_read_as_unsigned_32_bit(varid, raw, expected):
    status = [{"vartype": "value", "varid": varid, "varvalue": raw}]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    data = await device.get_status_data()
    assert data[f"status_{varid}"] == expected


async def test_packet_counter_outside_32_bit_range_is_refused():
    # Unterhalb von -2**31 kann es kein umgedeuteter 32-Bit-Zaehler sein.
    status = [{"vartype": "value", "varid": "txpackets", "varvalue": "-2147483649"}]
    device = Gfm2(StubApi(status=status), time_zone=BERLIN)
    data = await device.get_status_data()
    assert data["status_txpackets"] is None


async def test_extended_data_takes_the_read_value_over_the_placeholder():
    # Die Optikseite schickt jedes Feld doppelt: erst den Platzhalter der
    # Vorlage (12000 mV, 90 mA, 50 Grad), dann den gelesenen Wert.
    device = Gfm2(StubApi(extended=load_extended_fixture), time_zone=BERLIN)
    data = await device.get_extended_data()
    assert data["extended_optical_voltage"] == 3205.80
    assert data["extended_optical_bias_current"] == 0.0
    assert data["extended_optical_temperature"] == 31.05


async def test_extended_data_reads_state_and_system_values():
    device = Gfm2(StubApi(extended=load_extended_fixture), time_zone=BERLIN)
    data = await device.get_extended_data()
    assert data["extended_gpon_state"] == "O1"
    assert data["extended_cpu_usage"] == 0.0
    assert data["extended_memory_usage"] == 66.36
    assert data["extended_reboot_cause"] == "HW"
    assert data["extended_active_image"] == "FW1"


async def test_extended_data_carries_no_identifiers():
    # Die Seiten enthalten Seriennummern. Nichts davon darf in den Daten und
    # damit in der Diagnose landen.
    device = Gfm2(StubApi(extended=load_extended_fixture), time_zone=BERLIN)
    data = await device.get_extended_data()
    assert "53434F4D00C0FFEE" not in str(data)


async def test_extended_data_is_empty_when_the_modem_does_not_serve_it():
    def refuse(page):
        raise Gfm2ApiClientCommunicationError(page)

    device = Gfm2(
        StubApi(status=load_json_fixture("status_full.json"), extended=refuse),
        time_zone=BERLIN,
    )
    assert await device.get_extended_data() == {}
    # Die dokumentierten Werte bleiben davon unberuehrt.
    data = await device.get_all_data()
    assert data["status_rxpower"] == -16.13
    assert "extended_gpon_state" not in data


async def test_extended_data_tolerates_malformed_pages():
    device = Gfm2(
        StubApi(extended=lambda _page: {"unexpected": "shape"}), time_zone=BERLIN
    )
    assert await device.get_extended_data() == {}

    device = Gfm2(
        StubApi(extended=lambda _page: [{"gpon_status": "bogus"}, "noise", None]),
        time_zone=BERLIN,
    )
    data = await device.get_extended_data()
    assert data["extended_gpon_state"] is None
    assert data["extended_optical_temperature"] is None


def _load_fw013_fixture(page):
    # Ausgabe des Maintainers aus Issue #143 (Firmware 090144.1.0.013) fuer
    # die Seiten, die er gepostet hat. Die GPON-Seite fehlt dort.
    return load_json_fixture(
        {
            "statussupport_optical": "extended_optical_fw013.json",
            "statussupportstatus": "extended_status_fw013.json",
        }.get(page, "extended_gpon_no_link.json")
    )


async def test_extended_data_reads_firmware_013():
    device = Gfm2(StubApi(extended=_load_fw013_fixture), time_zone=BERLIN)
    data = await device.get_extended_data()
    assert data["extended_optical_voltage"] == 3221.40
    assert data["extended_optical_bias_current"] == 11.45
    assert data["extended_optical_temperature"] == 41.33
    assert data["extended_cpu_usage"] == 2.01
    assert data["extended_memory_usage"] == 69.49
    assert data["extended_reboot_cause"] == "SW"
    assert data["extended_active_image"] == "FW1"
    assert "53434F4D00C0FFEE" not in str(data)


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        # Tage:Stunden:Minuten, laut Maintainer in Issue #143.
        (load_extended_fixture, 3 * 60),
        (_load_fw013_fixture, ((6 * 24 + 13) * 60 + 51) * 60),
    ],
)
async def test_system_uptime_is_read_as_days_hours_minutes(fixture, expected):
    device = Gfm2(StubApi(extended=fixture), time_zone=BERLIN)
    data = await device.get_extended_data()
    assert data["extended_system_uptime"] == expected


@pytest.mark.parametrize(
    "raw", [None, "", "6:13", "6:13:51:00", "0:24:0", "0:0:60", "a:b:c", "-1:0:0"]
)
async def test_unreadable_system_uptime_is_unknown(raw):
    device = Gfm2(
        StubApi(extended=lambda _page: [{"sys_uptime": raw}]), time_zone=BERLIN
    )
    data = await device.get_extended_data()
    assert data["extended_system_uptime"] is None
