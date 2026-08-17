"""Diagnostics support for GFM2."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import Gfm2ConfigEntry

TO_REDACT = {"status_serial_number"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: Gfm2ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "entry_data": dict(entry.data),
        "data": async_redact_data(entry.runtime_data.coordinator.data, TO_REDACT),
    }
