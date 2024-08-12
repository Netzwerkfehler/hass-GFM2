"""Sensor platform for GFM2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONF_IP_ADDRESS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTime,
)

from .const import DOMAIN
from .entity import Gfm2Entity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import Gfm2DataUpdateCoordinator
    from .data import Gfm2ConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="status_txpackets",
        name="LAN Packets Sent",
        icon="mdi:package-up",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Packets",
    ),
    SensorEntityDescription(
        key="status_txbytes",
        name="LAN Data Sent",
        icon="mdi:upload",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.BYTES,
    ),
    SensorEntityDescription(
        key="status_rxpackets",
        name="LAN Packets Received",
        icon="mdi:package-down",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Packets",
    ),
    SensorEntityDescription(
        key="status_rxbytes",
        name="LAN Data Received",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.BYTES,
    ),
    SensorEntityDescription(
        key="status_rxdrop_packets",
        name="LAN Dropped Packets",
        icon="mdi:package-variant-closed-minus",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Packets",
    ),
    SensorEntityDescription(
        key="status_link_status",
        name="LAN Link",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    ),
    SensorEntityDescription(
        key="status_stability",
        name="LAN Link Uptime",
        icon="mdi:check-network",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    SensorEntityDescription(
        key="status_txpower",
        name="PON Tx Power",
        icon="mdi:upload-network",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ),
    SensorEntityDescription(
        key="status_rxpower",
        name="PON Rx Power",
        icon="mdi:download-network",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ),
    SensorEntityDescription(
        key="status_rxbip_crc",
        name="PON RxBiP / CRC",
        icon="mdi:timeline-alert",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="status_ui_version",
        name="UI Version",
        icon="mdi:web",
    ),
    SensorEntityDescription(
        key="firmware_firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="firmware_firmware_date",
        name="Firmware Date",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="custom_last_reboot",
        name="Last Reboot",
        icon="mdi:history",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: Gfm2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        Gfm2Sensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class Gfm2Sensor(Gfm2Entity, SensorEntity):
    """GFM2 Sensor class."""

    def __init__(
        self,
        coordinator: Gfm2DataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_name = f"{self.coordinator.config_entry.runtime_data.device.device_name} {entity_description.name}"  # noqa: E501
        self._attr_unique_id = f"{DOMAIN}_{coordinator.config_entry.data[CONF_IP_ADDRESS]}_{entity_description.key}"  # noqa: E501

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)
