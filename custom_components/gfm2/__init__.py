"""
Custom integration to integrate Glasfaser-Modem 2 with Home Assistant.

For more details about this integration, please refer to
https://github.com/Netzwerkfehler/hass-GFM2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration
from homeassistant.util import dt as dt_util

from .api import Gfm2ApiClient
from .coordinator import Gfm2DataUpdateCoordinator
from .data import Gfm2Data
from .gfm2 import Gfm2

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import Gfm2ConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: Gfm2ConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = Gfm2DataUpdateCoordinator(hass=hass)
    entry.runtime_data = Gfm2Data(
        device=Gfm2(
            Gfm2ApiClient(
                ip_address=entry.data[CONF_IP_ADDRESS],
                session=async_get_clientsession(hass),
            ),
            time_zone=dt_util.get_default_time_zone(),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()
    _async_adopt_serial_number(hass, entry)
    _async_migrate_device_identifiers(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: Gfm2ConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _async_adopt_serial_number(
    hass: HomeAssistant,
    entry: Gfm2ConfigEntry,
) -> None:
    """
    Claim the serial number as the entry's unique ID.

    Entries added before the config flow asked for it carry no unique ID, so
    the duplicate check in the flow cannot recognise them and the same modem
    can be set up a second time.
    """
    serial_number = entry.runtime_data.device.serial_number
    if not serial_number or entry.unique_id is not None:
        return
    hass.config_entries.async_update_entry(entry, unique_id=serial_number)


def _async_migrate_device_identifiers(
    hass: HomeAssistant,
    entry: Gfm2ConfigEntry,
) -> None:
    """
    Migrate the device identifier from the entry ID to the serial number.

    Updating the identifiers in place keeps the device ID, area, custom name,
    and all entity links intact.
    """
    serial_number = entry.runtime_data.device.serial_number
    if not serial_number:
        return
    device_registry = dr.async_get(hass)
    old_device = device_registry.async_get_device(
        identifiers={(entry.domain, entry.entry_id)}
    )
    if old_device is None:
        return
    if device_registry.async_get_device(identifiers={(entry.domain, serial_number)}):
        return
    device_registry.async_update_device(
        old_device.id,
        new_identifiers={(entry.domain, serial_number)},
    )
