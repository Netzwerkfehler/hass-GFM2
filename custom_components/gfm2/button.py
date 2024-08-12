"""Binary sensor platform for GFM2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import CONF_IP_ADDRESS

from .const import DOMAIN
from .entity import Gfm2Entity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import Gfm2DataUpdateCoordinator
    from .data import Gfm2ConfigEntry

ENTITY_DESCRIPTIONS = (
    ButtonEntityDescription(
        key="restart",
        name="Restart",
        device_class=ButtonDeviceClass.RESTART,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: Gfm2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities([Gfm2RebootButton(entry.runtime_data.coordinator)])


class Gfm2RebootButton(ButtonEntity, Gfm2Entity):
    """Reboot button."""

    def __init__(self, coordinator: Gfm2DataUpdateCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._attr_name = (
            f"{self.coordinator.config_entry.runtime_data.device.device_name} Restart"
        )
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.config_entry.data[CONF_IP_ADDRESS]}_reboot_restart"
        )

        self._attr_device_class = ButtonDeviceClass.RESTART

    async def async_press(self) -> None:
        """Send restart command."""
        await self.coordinator.config_entry.runtime_data.device.reboot()
