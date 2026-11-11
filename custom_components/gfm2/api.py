"""GFM2 API Client."""

from __future__ import annotations

import asyncio
import re
import socket
import time
from typing import Any

import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError

from .const import LOGGER

# The Sercomm pages write the token into their first script block.
_CSRF_TOKEN_PATTERN = re.compile(r"csrf_token\s*=\s*'([^']+)'")


class Gfm2ApiClientError(Exception):
    """Exception to indicate a general API error."""


class Gfm2ApiClientCommunicationError(
    Gfm2ApiClientError,
):
    """Exception to indicate a communication error."""


class Gfm2ApiClient:
    """GFM2 API Client."""

    def __init__(
        self,
        ip_address: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """GFM2 API Client."""
        self._ip_address = ip_address
        self._session = session
        self._csrf_token: str | None = None

    async def async_get_status_data(self) -> Any:
        """Get status data from the API."""
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._ip_address}/ONT/client/data/Status.json",
            headers={"Accept-Language": "en"},
        )

    async def async_get_firmware_data(self) -> Any:
        """Get firmware status data from the API."""
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._ip_address}/ONT/client/data/FirmwareUpdate.json",
            headers={"Accept-Language": "en"},
        )

    async def async_get_reboot_data(self) -> Any:
        """Get reboot status data from the API."""
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._ip_address}/ONT/client/data/Reboot.json",
            headers={"Accept-Language": "en"},
        )

    async def async_get_extended_data(self, page: str) -> Any:
        """
        Get one page of the extended status data.

        Below the Telekom pages the modem still serves the status pages of the
        Sercomm base firmware. They need no login, only the token that every
        such page carries. The token stays valid across requests, so it is
        fetched once and again only after a request with it has failed: the
        modem answers a wrong token by closing the connection.
        """
        if self._csrf_token is None:
            self._csrf_token = await self._async_fetch_csrf_token()
        try:
            return await self._async_get_extended_page(page, self._csrf_token)
        except Gfm2ApiClientCommunicationError:
            self._csrf_token = None
            self._csrf_token = await self._async_fetch_csrf_token()
            return await self._async_get_extended_page(page, self._csrf_token)

    async def _async_fetch_csrf_token(self) -> str:
        """Read the token from a status page of the Sercomm base firmware."""
        html = await self._api_wrapper(
            method="get",
            url=f"http://{self._ip_address}/setup.cgi?next_file=statusandsupport/status.html",
            headers={"Accept-Language": "en"},
            response_format="text",
        )
        match = _CSRF_TOKEN_PATTERN.search(html)
        if match is None:
            msg = "The status page carries no token"
            raise Gfm2ApiClientError(msg)
        return match.group(1)

    async def _async_get_extended_page(self, page: str, csrf_token: str) -> Any:
        """Get one page of the Sercomm base firmware."""
        # The first parameter is the cache buster the modem's own pages send.
        query = f"_={int(time.time() * 1000)}&csrf_token={csrf_token}"
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._ip_address}/data/{page}.json?{query}",
            headers={"Accept-Language": "en"},
            response_format="sercomm_json",
        )

    async def async_do_reboot(self) -> Any:
        """Trigger a reboot from the API."""
        try:
            return await self._api_wrapper(
                method="post",
                url=f"http://{self._ip_address}/ONT/client/data/Reboot.json",
                headers={"Accept-Language": "en"},
                data={"reboot_device": "true"},
            )
        except Gfm2ApiClientCommunicationError as exception:
            # Device disconnects during reboot before sending a response,
            # causing ServerDisconnectedError. This is (unfortunately)
            # expected behavior.
            if isinstance(exception.__cause__, ServerDisconnectedError):
                LOGGER.info("Device is rebooting (server disconnected)")
                return True
            raise

    async def _api_wrapper(  # noqa: PLR0913 One more than allowed, all of them plain
        self,
        method: str,
        url: str,
        json: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        response_format: str = "telekom_json",
    ) -> Any:
        """Get information from the API."""
        try:
            async with asyncio.timeout(10):
                response = await self._session.request(
                    method=method, url=url, headers=headers, json=json, data=data
                )
                if response_format == "text":
                    return await response.text()
                if response_format == "sercomm_json":
                    # These pages come as text/html.
                    return await response.json(content_type=None)
                return await response.json(content_type="application/javascript")

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise Gfm2ApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise Gfm2ApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise Gfm2ApiClientError(
                msg,
            ) from exception
