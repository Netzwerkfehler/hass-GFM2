"""Tests for integration setup and unload."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.gfm2.const import DOMAIN

from .conftest import TEST_SERIAL, load_json_fixture

EXPECTED_ENTITY_COUNT = 18


async def test_setup_creates_all_entities(hass, config_entry, mock_api):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.update_listeners == []
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    assert len(entries) == EXPECTED_ENTITY_COUNT


async def test_unload_entry(hass, config_entry, mock_api):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_adopts_the_serial_number_as_unique_id(
    hass, config_entry, mock_api
):
    """An entry from before the serial number was claimed must adopt it."""
    config_entry.add_to_hass(hass)
    assert config_entry.unique_id is None

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.unique_id == TEST_SERIAL


async def test_missing_versions_never_reach_the_device_page(
    hass, config_entry, mock_api, device_registry
):
    # Sonst steht "None / UI: None" auf der Geraeteseite.
    mock_api["status"].return_value = load_json_fixture("status_incomplete.json")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.entry_id)}
    )
    assert device is not None
    # Die UI-Version steht in status.json und fehlt hier, die Firmware-Version
    # kommt vom eigenen Endpunkt und bleibt erhalten.
    assert device.sw_version == "090144.1.0.001"


async def test_no_versions_at_all_leave_the_software_version_empty(
    hass, config_entry, mock_api, device_registry
):
    mock_api["status"].return_value = load_json_fixture("status_incomplete.json")
    mock_api["firmware"].return_value = []
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.entry_id)}
    )
    assert device is not None
    assert device.sw_version is None


async def test_device_identity_migrates_without_creating_a_second_device(
    hass, config_entry, mock_api, device_registry
):
    config_entry.add_to_hass(hass)
    old_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, config_entry.entry_id)},
        name="Glasfaser-Modem 2",
    )
    device_registry.async_update_device(old_device.id, name_by_user="Mein ONT")

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    migrated = device_registry.async_get_device(identifiers={(DOMAIN, TEST_SERIAL)})
    assert migrated is not None
    assert migrated.id == old_device.id, "Geraet wurde neu angelegt statt migriert"
    assert migrated.name_by_user == "Mein ONT"
    assert migrated.model == "FG1000B.11"
    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
        is None
    )

    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    assert len(devices) == 1, "Geistergeraet zurueckgeblieben"
