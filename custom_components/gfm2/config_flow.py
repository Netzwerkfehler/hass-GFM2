"""Adds config flow for GFM2."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import (
    Gfm2ApiClient,
    Gfm2ApiClientCommunicationError,
    Gfm2ApiClientError,
)
from .const import DOMAIN, LOGGER
from .gfm2 import Gfm2


class Gfm2FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for GFM2."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            # Entries from before the serial number was claimed carry no unique
            # ID. A disabled one never runs its setup and never adopts one
            # either, so the check below cannot see it. Its address can.
            if any(
                entry.data.get(CONF_IP_ADDRESS) == user_input[CONF_IP_ADDRESS]
                for entry in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")
            try:
                status = await self._get_status_data(
                    ip_address=user_input[CONF_IP_ADDRESS]
                )
            except Gfm2ApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except Gfm2ApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                serial_number = status.get("status_serial_number")
                if serial_number:
                    await self.async_set_unique_id(str(serial_number))
                    self._abort_if_unique_id_configured()
                device_name = status.get("status_device_name") or "Glasfaser-Modem 2"
                return self.async_create_entry(
                    title=f"{device_name} ({user_input[CONF_IP_ADDRESS]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IP_ADDRESS,
                        default=(user_input or {}).get(
                            CONF_IP_ADDRESS, "192.168.100.1"
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    )
                },
            ),
            errors=_errors,
        )

    async def _get_status_data(self, ip_address: str) -> dict[str, object]:
        """Check the connection and return the status payload."""
        device = Gfm2(
            Gfm2ApiClient(
                ip_address=ip_address,
                session=async_get_clientsession(self.hass),
            ),
            time_zone=dt_util.get_default_time_zone(),
        )
        return await device.get_status_data()
