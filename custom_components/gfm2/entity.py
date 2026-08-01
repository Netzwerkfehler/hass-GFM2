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

        device = coordinator.config_entry.runtime_data.device
        serial_number = device.serial_number
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    serial_number or coordinator.config_entry.entry_id,
                ),
            },
            manufacturer="Telekom (OEM: Sercomm)",
            # The hardware revision is only "V1" and already appears below.
            # Keep the more useful Sercomm model identifier here.
            model="FG1000B.11",
            serial_number=serial_number,
            name=device.device_name,
            hw_version=device.hardware_revision,
            sw_version=f"{device.firmware_version} / UI: {device.ui_version}",
            configuration_url=f"http://{coordinator.config_entry.data[CONF_IP_ADDRESS]}/ONT/client/html/content/overview/index.html",
        )
