"""Gfm2Entity class."""

from __future__ import annotations

from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import Gfm2DataUpdateCoordinator


class Gfm2Entity(CoordinatorEntity[Gfm2DataUpdateCoordinator]):
    """Gfm2Entity class."""

    def __init__(self, coordinator: Gfm2DataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            manufacturer="Telekom (OEM: Sercomm)",
            model="FG1000B.11",
            serial_number=coordinator.config_entry.runtime_data.device.serial_number,
            name=coordinator.config_entry.runtime_data.device.device_name,
            hw_version=coordinator.config_entry.runtime_data.device.hardware_revision,
            sw_version=f"{coordinator.config_entry.runtime_data.device.firmware_version} / UI: {coordinator.config_entry.runtime_data.device.ui_version}",  # noqa: E501
            configuration_url=f"http://{coordinator.config_entry.data[CONF_IP_ADDRESS]}/ONT/client/html/content/overview/index.html",
        )
