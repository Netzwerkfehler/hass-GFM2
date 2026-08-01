"""Tests for integration setup and unload."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.gfm2 import async_reload_entry
from custom_components.gfm2.const import DOMAIN

from .conftest import TEST_SERIAL

# Wird in Task 13 auf 19 erhöht, wenn der PON-Status-Sensor dazukommt.
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


async def test_reload_entry_uses_home_assistant_api(hass, config_entry):
    with (
        patch(
            "custom_components.gfm2.async_unload_entry",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.gfm2.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
        patch.object(
            hass.config_entries,
            "async_reload",
            new=AsyncMock(return_value=True),
        ) as async_reload,
    ):
        await async_reload_entry(hass, config_entry)

    async_reload.assert_awaited_once_with(config_entry.entry_id)


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
