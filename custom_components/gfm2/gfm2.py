"""Module that abstracts some device API's."""

from datetime import datetime
from zoneinfo import ZoneInfo

from .api import Gfm2ApiClient


class Gfm2:
    """Class the abstracts some device API's."""

    def __init__(self, api: Gfm2ApiClient) -> None:
        """Init."""
        self._api: Gfm2ApiClient = api
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

        # invert value
        data["status_hardware_state"] = data["status_hardware_state"] != "1"

        # custom value to for fiber link; rx and tx become "--" when disconnected
        data["custom_fiber_connection"] = (
            data["status_txpower"] != "--" and data["status_rxpower"] != "--"
        )

        if data["status_txpower"] == "--":
            data["status_txpower"] = None

        if data["status_rxpower"] == "--":
            data["status_rxpower"] = None

        return data

    async def get_firmware_data(self) -> dict[str, object]:
        """Read data from the firmware.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_firmware_data(), "firmware")
        data["firmware_firmware_date"] = datetime.strptime(
            str(data["firmware_firmware_date"]), "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=ZoneInfo("UTC"))
        return data

    async def get_reboot_data(self) -> dict[str, object]:
        """Read data from the reboot.json endpoint."""
        data = Gfm2.process_json(await self._api.async_get_reboot_data(), "reboot")
        data["custom_last_reboot"] = datetime.strptime(
            f"{data["reboot_reboot_date"]} {data["reboot_reboot_time"]}",
            "%d.%m.%Y %H:%M",
        ).replace(tzinfo=ZoneInfo("UTC"))
        return data

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
    def serial_number(self) -> str:
        """Returns the serial number."""
        return str(self._all_data["status_serial_number"])

    @property
    def device_name(self) -> str:
        """Returns the device name."""
        return str(self._all_data["status_device_name"])

    @property
    def hardware_revision(self) -> str:
        """Returns the hardare revision."""
        return str(self._all_data["status_hardware_revision"])

    @property
    def ui_version(self) -> str:
        """Returns the UI version."""
        return str(self._all_data["status_ui_version"])

    @property
    def firmware_version(self) -> str:
        """Returns the firmware version."""
        return str(self._all_data["firmware_firmware_version"])

    @staticmethod
    def process_json(json_data, prefix: str) -> dict[str, object]:  # noqa: ANN001
        """Flattens the given json structure."""
        flattened_data: dict[str, object] = {}

        for kvp in json_data:
            flattened_data[f"{prefix}_{kvp.get("varid")}"] = kvp.get("varvalue")

        return flattened_data
