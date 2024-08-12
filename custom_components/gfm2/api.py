"""GFM2 API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout


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

    async def async_do_reboot(self) -> Any:
        """Trigger a reboot from the API."""
        return await self._api_wrapper(
            method="post",
            url=f"http://{self._ip_address}/ONT/client/data/Reboot.json",
            headers={"Accept-Language": "en"},
            data={"Reboot": "true"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
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
