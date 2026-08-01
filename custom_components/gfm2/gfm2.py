"""Module that abstracts some device API's."""

from __future__ import annotations

from datetime import datetime, tzinfo
from typing import TYPE_CHECKING

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


def _to_int(value: object) -> int | None:
    """
    Convert a value to an integer.

    Return None when the value is not numeric.
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: object) -> float | None:
    """
    Convert a value to a float.

    Return None when the value is not numeric.
    """
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


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
        self._all_data = all_data
        return all_data

    async def get_status_data(self) -> dict[str, object]:
        """Read data from the status.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_status_data(), "status")

        # "0" means hardware fault; any other value (including absent) is OK.
        data["status_hardware_state"] = data.get("status_hardware_state") == "0"

        # rx and tx power become "--" when the fiber link is down. Deriving the
        # link state from the parsed numbers keeps it consistent with the two
        # power sensors: anything that is not a number leaves all three unknown.
        txpower = _to_float(data.get("status_txpower"))
        rxpower = _to_float(data.get("status_rxpower"))
        data["custom_fiber_connection"] = txpower is not None and rxpower is not None
        data["status_txpower"] = txpower
        data["status_rxpower"] = rxpower

        # The 2020 firmware reports the negotiated speed in Mbit/s, but only up
        # to 1000. Faster links read "0" instead; measured at 2.5G and at 5G,
        # while a 1G link reports "1000".
        if data.get("status_link_status") == "0":
            data["status_link_status"] = None

        for key in _INT_KEYS:
            data[key] = _to_int(data.get(key))
        for key in _FLOAT_KEYS:
            data[key] = _to_float(data.get(key))

        return data

    async def get_firmware_data(self) -> dict[str, object]:
        """Read data from the firmware.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_firmware_data(), "firmware")
        data["firmware_firmware_date"] = self._parse_device_datetime(
            str(data.get("firmware_firmware_date")), "%Y-%m-%d %H:%M:%S"
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

    def _parse_device_datetime(self, raw: str, fmt: str) -> datetime | None:
        """Parse a device timestamp in the configured time zone, None on failure."""
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=self._time_zone)
        except ValueError:
            return None

    async def reboot(self) -> None:
        """Reboots the modem."""
        await self._api.async_do_reboot()

    async def test(self) -> bool:
        """Test the connection."""
        return await self._api.async_get_status_data() is not None

    def get_data_dict(self) -> dict[str, object]:
        """Return the data dict."""
        return self._all_data

    @property
    def serial_number(self) -> str | None:
        """Returns the serial number."""
        value = self._all_data.get("status_serial_number")
        return None if value is None else str(value)

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
