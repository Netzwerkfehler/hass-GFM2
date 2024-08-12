"""
Custom integration to integrate Glasfaser-Modem 2 with Home Assistant.

For more details about this integration, please refer to
https://github.com/Netzwerkfehler/hass-GFM2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from custom_components.gfm2.gfm2 import Gfm2

from .api import Gfm2ApiClient
from .coordinator import Gfm2DataUpdateCoordinator
from .data import Gfm2Data

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
            )
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(
    hass: HomeAssistant,
    entry: Gfm2ConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: Gfm2ConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
