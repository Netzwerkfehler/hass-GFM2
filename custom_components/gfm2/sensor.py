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
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import Gfm2DataUpdateCoordinator
    from .data import Gfm2ConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="status_txpackets",
        translation_key="lan_packets_sent",
        icon="mdi:package-up",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Packets",
    ),
    SensorEntityDescription(
        key="status_txbytes",
        translation_key="lan_data_sent",
        icon="mdi:upload",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.BYTES,
    ),
    SensorEntityDescription(
        key="status_rxpackets",
        translation_key="lan_packets_received",
        icon="mdi:package-down",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Packets",
    ),
    SensorEntityDescription(
        key="status_rxbytes",
        translation_key="lan_data_received",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfInformation.BYTES,
    ),
    SensorEntityDescription(
        key="status_rxdrop_packets",
        translation_key="lan_dropped_packets",
        icon="mdi:package-variant-closed-minus",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="Packets",
    ),
    SensorEntityDescription(
        key="status_link_status",
        translation_key="lan_link",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    ),
    SensorEntityDescription(
        key="status_stability",
        translation_key="lan_link_uptime",
        icon="mdi:check-network",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
    ),
    SensorEntityDescription(
        key="status_txpower",
        translation_key="pon_tx_power",
        icon="mdi:upload-network",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ),
    SensorEntityDescription(
        key="status_rxpower",
        translation_key="pon_rx_power",
        icon="mdi:download-network",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ),
    SensorEntityDescription(
        key="status_rxbip_crc",
        translation_key="pon_rxbip_crc",
        icon="mdi:timeline-alert",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="status_ui_version",
        translation_key="ui_version",
        icon="mdi:web",
    ),
    SensorEntityDescription(
        key="firmware_firmware_version",
        translation_key="firmware_version",
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="firmware_firmware_date",
        translation_key="firmware_date",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="custom_last_reboot",
        translation_key="last_reboot",
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

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Gfm2DataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{coordinator.config_entry.data[CONF_IP_ADDRESS]}_{entity_description.key}"  # noqa: E501

    @property
    def native_value(self) -> StateType | datetime:
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)
