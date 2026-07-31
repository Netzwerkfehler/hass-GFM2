"""Compatibility guard: existing entity ids and names must never change."""

from custom_components.gfm2.const import DOMAIN

from .conftest import TEST_IP

# (domain, unique_id, erwartete object_id, erwarteter Friendly Name)
# Stand einer Bestandsinstallation vor diesem Branch. NIEMALS anpassen,
# um einen roten Test gruen zu bekommen: rot heisst, der Umbau bricht Nutzer.
OLD_ENTITIES = [
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_txpackets",
        "glasfaser_modem_2_lan_packets_sent",
        "Glasfaser-Modem 2 LAN Packets Sent",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_txbytes",
        "glasfaser_modem_2_lan_data_sent",
        "Glasfaser-Modem 2 LAN Data Sent",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_rxpackets",
        "glasfaser_modem_2_lan_packets_received",
        "Glasfaser-Modem 2 LAN Packets Received",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_rxbytes",
        "glasfaser_modem_2_lan_data_received",
        "Glasfaser-Modem 2 LAN Data Received",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_rxdrop_packets",
        "glasfaser_modem_2_lan_dropped_packets",
        "Glasfaser-Modem 2 LAN Dropped Packets",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_link_status",
        "glasfaser_modem_2_lan_link",
        "Glasfaser-Modem 2 LAN Link",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_stability",
        "glasfaser_modem_2_lan_link_uptime",
        "Glasfaser-Modem 2 LAN Link Uptime",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_txpower",
        "glasfaser_modem_2_pon_tx_power",
        "Glasfaser-Modem 2 PON Tx Power",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_rxpower",
        "glasfaser_modem_2_pon_rx_power",
        "Glasfaser-Modem 2 PON Rx Power",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_rxbip_crc",
        "glasfaser_modem_2_pon_rxbip_crc",
        "Glasfaser-Modem 2 PON RxBiP / CRC",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_status_ui_version",
        "glasfaser_modem_2_ui_version",
        "Glasfaser-Modem 2 UI Version",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_firmware_firmware_version",
        "glasfaser_modem_2_firmware_version",
        "Glasfaser-Modem 2 Firmware Version",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_firmware_firmware_date",
        "glasfaser_modem_2_firmware_date",
        "Glasfaser-Modem 2 Firmware Date",
    ),
    (
        "sensor",
        f"{DOMAIN}_{TEST_IP}_custom_last_reboot",
        "glasfaser_modem_2_last_reboot",
        "Glasfaser-Modem 2 Last Reboot",
    ),
    (
        "binary_sensor",
        f"{DOMAIN}_{TEST_IP}_status_hardware_state",
        "glasfaser_modem_2_hardware_status",
        "Glasfaser-Modem 2 Hardware Status",
    ),
    (
        "binary_sensor",
        f"{DOMAIN}_{TEST_IP}_firmware_autofw_active",
        "glasfaser_modem_2_automatic_firmware_updates",
        "Glasfaser-Modem 2 Automatic Firmware Updates",
    ),
    (
        "binary_sensor",
        f"{DOMAIN}_{TEST_IP}_custom_fiber_connection",
        "glasfaser_modem_2_fiber_connection",
        "Glasfaser-Modem 2 Fiber Connection",
    ),
    (
        "button",
        f"{DOMAIN}_{TEST_IP}_reboot_restart",
        "glasfaser_modem_2_restart",
        "Glasfaser-Modem 2 Restart",
    ),
]


async def test_existing_entity_ids_and_names_are_preserved(
    hass, config_entry, mock_api, entity_registry
):
    config_entry.add_to_hass(hass)

    # Registry wie bei einer Bestandsinstallation vorbefuellen.
    for domain, unique_id, object_id, old_name in OLD_ENTITIES:
        entity_registry.async_get_or_create(
            domain,
            DOMAIN,
            unique_id,
            suggested_object_id=object_id,
            original_name=old_name,
            config_entry=config_entry,
        )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for domain, unique_id, object_id, old_name in OLD_ENTITIES:
        entity_id = entity_registry.async_get_entity_id(domain, DOMAIN, unique_id)
        assert entity_id == f"{domain}.{object_id}", (
            f"entity_id fuer {unique_id} hat sich geaendert: {entity_id}"
        )
        state = hass.states.get(entity_id)
        assert state is not None, f"{entity_id} hat keinen State"
        assert state.attributes.get("friendly_name") == old_name

    # Es darf keine Duplikat-Entities mit _2-Suffix geben.
    for entity_id in hass.states.async_entity_ids():
        assert not entity_id.endswith("_2"), f"Duplikat erzeugt: {entity_id}"
