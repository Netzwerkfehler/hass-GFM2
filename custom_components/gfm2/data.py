"""Custom types for GFM2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from custom_components.gfm2.gfm2 import Gfm2

    from .coordinator import Gfm2DataUpdateCoordinator


type Gfm2ConfigEntry = ConfigEntry[Gfm2Data]


@dataclass
class Gfm2Data:
    """Data for the GFM2 integration."""

    device: Gfm2
    coordinator: Gfm2DataUpdateCoordinator
    integration: Integration
