"""Module that abstracts some device API's."""

from __future__ import annotations

import math
import re
from datetime import datetime, tzinfo
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from .api import Gfm2ApiClientError
from .const import LOGGER

if TYPE_CHECKING:
    from .api import Gfm2ApiClient

_INT_KEYS = (
    "status_txpackets",
    "status_txbytes",
    "status_rxpackets",
    "status_rxbytes",
    "status_rxdrop_packets",
    "status_stability",
    "status_rxbip_crc",
)
_FLOAT_KEYS = ("status_txpower", "status_rxpower")
# The modem keeps its packet counters in 32 bits but prints them signed, so a
# counter past 2**31 shows up negative while it keeps counting.
_UINT32_KEYS = ("status_txpackets", "status_rxpackets", "status_rxdrop_packets")
_INT32_MIN = -(2**31)
_UINT32_RANGE = 2**32

# Status pages of the Sercomm base firmware, see get_extended_data.
_EXTENDED_PAGES = (
    "statussupport_gpon",
    "statussupport_optical",
    "statussupportstatus",
)
_GPON_STATE_PATTERN = re.compile(r"O[1-7]")
# sys_uptime is days:hours:minutes, e.g. "6:13:51".
_UPTIME_PATTERN = re.compile(r"(\d+):(\d+):(\d+)")


def _to_int(value: object) -> int | None:
    """
    Convert a value to an integer.

    Return None when the value is not numeric.
    """
    try:
        return int(str(value))
    except TypeError, ValueError:
        return None


def _to_float(value: object) -> float | None:
    """
    Convert a value to a float.

    Return None when the value is not a finite number. "NaN" and "Infinity"
    parse happily but would travel on into sensor states and long-term
    statistics, so they count as no reading at all.
    """
    try:
        number = float(str(value))
    except TypeError, ValueError:
        return None
    return number if math.isfinite(number) else None


def _to_uint32(value: int | None) -> int | None:
    """
    Read a signed 32-bit counter as unsigned.

    Return None for a negative value that no 32-bit counter can produce.
    """
    if value is None or value >= 0:
        return value
    if value < _INT32_MIN:
        return None
    return value + _UINT32_RANGE


def _to_percent(value: object) -> float | None:
    """Convert a value like "66.36%" to a float, None when it is no number."""
    return _to_float(str(value).strip().removesuffix("%"))


def _to_uptime_seconds(value: object) -> int | None:
    """Convert an uptime like "6:13:51" (days:hours:minutes) to seconds."""
    match = _UPTIME_PATTERN.fullmatch(str(value).strip())
    if match is None:
        return None
    days, hours, minutes = (int(part) for part in match.groups())
    if hours >= 24 or minutes >= 60:  # noqa: PLR2004 hours per day, minutes per hour
        return None
    return ((days * 24 + hours) * 60 + minutes) * 60


def _to_text(value: object) -> str | None:
    """Return a non-empty string, None for anything else."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


class Gfm2:
    """Class the abstracts some device API's."""

    def __init__(self, api: Gfm2ApiClient, time_zone: tzinfo) -> None:
        """Init."""
        self._api: Gfm2ApiClient = api
        self._time_zone = time_zone
        self._all_data: dict[str, object] = {}

    async def get_all_data(self) -> dict[str, object]:
        """Read data from all endpoints."""
        all_data: dict[str, object] = {}
        all_data.update(await self.get_status_data())
        all_data.update(await self.get_firmware_data())
        all_data.update(await self.get_reboot_data())
        all_data.update(await self.get_extended_data())
        self._all_data = all_data
        return all_data

    async def get_status_data(self) -> dict[str, object]:
        """Read data from the status.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_status_data(), "status")

        # "0" means hardware fault; any other value (including absent) is OK.
        data["status_hardware_state"] = data.get("status_hardware_state") == "0"

        # rx and tx power become "--" when the fiber link is down, which is the
        # only field on this device that tells a live link from a dead one. The
        # power sensors turn unknown, and anything that does not parse as a
        # number counts as no link, including a response that omits the fields.
        txpower = _to_float(data.get("status_txpower"))
        rxpower = _to_float(data.get("status_rxpower"))
        data["custom_fiber_connection"] = txpower is not None and rxpower is not None
        data["status_txpower"] = txpower
        data["status_rxpower"] = rxpower

        # Firmware 2020 incorrectly reports "0" for a live 2.5G LAN link.
        if data.get("status_link_status") == "0":
            data["status_link_status"] = None

        for key in _INT_KEYS:
            data[key] = _to_int(data.get(key))
        for key in _UINT32_KEYS:
            data[key] = _to_uint32(data[key])
        for key in _FLOAT_KEYS:
            data[key] = _to_float(data.get(key))

        return data

    async def get_firmware_data(self) -> dict[str, object]:
        """Read data from the firmware.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_firmware_data(), "firmware")
        data["firmware_firmware_date"] = self._parse_device_datetime(
            str(data.get("firmware_firmware_date")),
            "%Y-%m-%d %H:%M:%S",
        )
        return data

    async def get_reboot_data(self) -> dict[str, object]:
        """Read data from the reboot.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_reboot_data(), "reboot")
        data["custom_last_reboot"] = self._parse_device_datetime(
            f"{data.get('reboot_reboot_date')} {data.get('reboot_reboot_time')}",
            "%d.%m.%Y %H:%M",
        )
        return data

    async def get_extended_data(self) -> dict[str, object]:
        """
        Read the status pages of the Sercomm base firmware.

        These pages are not part of the Telekom interface, so nothing here may
        take the documented sensors down with it: a modem that does not serve
        them yields an empty dict and the caller carries on.
        """
        raw: dict[str, object] = {}
        try:
            for page in _EXTENDED_PAGES:
                raw.update(
                    Gfm2.process_extended_json(
                        await self._api.async_get_extended_data(page)
                    )
                )
        except Gfm2ApiClientError as exception:
            LOGGER.debug("Extended status data not available: %s", exception)
            return {}
        if not raw:
            return {}

        gpon_state = str(raw.get("gpon_status"))
        return {
            "extended_gpon_state": (
                gpon_state if _GPON_STATE_PATTERN.fullmatch(gpon_state) else None
            ),
            "extended_optical_temperature": _to_float(
                raw.get("working_temperature_query")
            ),
            "extended_optical_voltage": _to_float(raw.get("working_voltage_query")),
            "extended_optical_bias_current": _to_float(
                raw.get("working_current_query")
            ),
            "extended_cpu_usage": _to_percent(raw.get("sys_cpu_usage")),
            "extended_memory_usage": _to_percent(raw.get("sys_memory_usage")),
            "extended_system_uptime": _to_uptime_seconds(raw.get("sys_uptime")),
            "extended_reboot_cause": _to_text(raw.get("sys_reboot_cause")),
            "extended_active_image": _to_text(raw.get("sys_current_image")),
        }

    def _parse_device_datetime(self, raw: str, fmt: str) -> datetime | None:
        """Parse a device timestamp in the configured time zone, None on failure."""
        # 'reboot_reboot_time' is reported in UTC, so 'firmware_firmware_date' will
        # also be until somebody proves me wrong.
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=ZoneInfo("UTC"))
        except ValueError:
            return None

    async def reboot(self) -> None:
        """Reboots the modem."""
        await self._api.async_do_reboot()

    def get_data_dict(self) -> dict[str, object]:
        """Return the data dict."""
        return self._all_data

    @property
    def serial_number(self) -> str | None:
        """
        Returns the serial number.

        The entry and the device are permanently identified by this value, so
        only a plain, non-empty string counts. Stringifying whatever a broken
        response left behind would migrate an installation onto that remnant.
        """
        value = self._all_data.get("status_serial_number")
        if not isinstance(value, str) or not value.strip():
            return None
        return value.strip()

    @property
    def device_name(self) -> str | None:
        """Returns the device name."""
        value = self._all_data.get("status_device_name")
        return None if value is None else str(value)

    @property
    def hardware_revision(self) -> str | None:
        """Returns the hardare revision."""
        value = self._all_data.get("status_hardware_revision")
        return None if value is None else str(value)

    @property
    def ui_version(self) -> str | None:
        """Returns the UI version."""
        value = self._all_data.get("status_ui_version")
        return None if value is None else str(value)

    @property
    def firmware_version(self) -> str | None:
        """Returns the firmware version."""
        value = self._all_data.get("firmware_firmware_version")
        return None if value is None else str(value)

    @staticmethod
    def process_json(json_data: object, prefix: str) -> dict[str, object]:
        """Flattens the given json structure, tolerating malformed input."""
        flattened_data: dict[str, object] = {}
        if not isinstance(json_data, list):
            return flattened_data
        for kvp in json_data:
            if not isinstance(kvp, dict):
                continue
            varid = kvp.get("varid")
            if not varid:
                continue
            flattened_data[f"{prefix}_{varid}"] = kvp.get("varvalue")

        return flattened_data

    @staticmethod
    def process_extended_json(json_data: object) -> dict[str, object]:
        """
        Flatten a page of the Sercomm base firmware, tolerating malformed input.

        A page is a list of objects with one key each. Several pages send every
        key twice: first the placeholder from the page template, then the value
        the modem actually read. The later one therefore wins.
        """
        flattened_data: dict[str, object] = {}
        if not isinstance(json_data, list):
            return flattened_data
        for item in json_data:
            if isinstance(item, dict):
                flattened_data.update(item)

        return flattened_data
