"""Sensor platform for GFM2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONF_IP_ADDRESS,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfDataRate,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfInformation,
    UnitOfTemperature,
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
        # Bytes stay native so statistics keep their base. A modem that has
        # been up for weeks reports thirteen digits, which reads as noise.
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
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
        # Bytes stay native so statistics keep their base. A modem that has
        # been up for weeks reports thirteen digits, which reads as noise.
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
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
        # link speed needs no decimal places
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="status_stability",
        translation_key="lan_link_uptime",
        icon="mdi:check-network",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        # Without this, the conversion from seconds leaves 13 decimals on screen.
        suggested_display_precision=2,
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

# Read from the status pages of the Sercomm base firmware. A modem that does
# not serve them gets none of these entities.
EXTENDED_ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="extended_gpon_state",
        translation_key="pon_state",
        icon="mdi:state-machine",
        device_class=SensorDeviceClass.ENUM,
        options=["O1", "O2", "O3", "O4", "O5", "O6", "O7"],
    ),
    SensorEntityDescription(
        key="extended_optical_temperature",
        translation_key="pon_optics_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_optical_voltage",
        translation_key="pon_optics_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_optical_bias_current",
        translation_key="pon_laser_bias_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_cpu_usage",
        translation_key="cpu_usage",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_memory_usage",
        translation_key="memory_usage",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_system_uptime",
        translation_key="system_uptime",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        # The modem counts in minutes, two decimals of a day are close to that.
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_reboot_cause",
        translation_key="reboot_cause",
        icon="mdi:restart-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="extended_active_image",
        translation_key="active_firmware_image",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: Gfm2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    # The extended keys come as a set, so one of them tells whether the modem
    # serves those pages at all.
    descriptions = ENTITY_DESCRIPTIONS
    if "extended_gpon_state" in coordinator.data:
        descriptions += EXTENDED_ENTITY_DESCRIPTIONS
    async_add_entities(
        Gfm2Sensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in descriptions
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
