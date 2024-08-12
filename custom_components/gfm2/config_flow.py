"""Adds config flow for GFM2."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from custom_components.gfm2.gfm2 import Gfm2

from .api import (
    Gfm2ApiClient,
    Gfm2ApiClientCommunicationError,
    Gfm2ApiClientError,
)
from .const import DOMAIN, LOGGER


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
            try:
                await self._test_connection(ip_address=user_input[CONF_IP_ADDRESS])
            except Gfm2ApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except Gfm2ApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_IP_ADDRESS],
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

    async def _test_connection(self, ip_address: str) -> None:
        """Check the connection."""
        device = Gfm2(
            Gfm2ApiClient(
                ip_address=ip_address,
                session=async_create_clientsession(self.hass),
            )
        )
        await device.test()
