"""Binary sensor platform for GFM2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
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
    BinarySensorEntityDescription(
        key="status_hardware_state",
        name="Hardware Status",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="firmware_autofw_active",
        name="Automatic Firmware Updates",
    ),
    BinarySensorEntityDescription(
        key="custom_fiber_connection",
        name="Fiber Connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: Gfm2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        Gfm2BinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class Gfm2BinarySensor(Gfm2Entity, BinarySensorEntity):
    """GFM2 binary_sensor class."""

    def __init__(
        self,
        coordinator: Gfm2DataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_name = f"{self.coordinator.config_entry.runtime_data.device.device_name} {entity_description.name}"  # noqa: E501
        self._attr_unique_id = f"{DOMAIN}_{coordinator.config_entry.data[CONF_IP_ADDRESS]}_{entity_description.key}"  # noqa: E501

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self.coordinator.data.get(self.entity_description.key, "") in ("1", True)
