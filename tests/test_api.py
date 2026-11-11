"""Tests for the API client against a mocked modem."""

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.gfm2.api import Gfm2ApiClient, Gfm2ApiClientError

from .conftest import TEST_IP

TOKEN_PAGE = f"http://{TEST_IP}/setup.cgi?next_file=statusandsupport/status.html"
OPTICAL_PAGE = f"http://{TEST_IP}/data/statussupport_optical.json"
# So steht das Token im ersten Skriptblock jeder Sercomm-Seite.
STATUS_PAGE_HTML = "<html><head><script>\n\t\tcsrf_token = 'TESTTOKEN123';\n</script>"


async def test_extended_data_sends_the_token_from_the_status_page(hass, aioclient_mock):
    aioclient_mock.get(TOKEN_PAGE, text=STATUS_PAGE_HTML)
    # Das Modem liefert diese Seiten als text/html aus.
    aioclient_mock.get(
        OPTICAL_PAGE,
        text='[ { "working_temperature_query": "31.05" } ]',
        headers={"Content-Type": "text/html"},
    )
    client = Gfm2ApiClient(TEST_IP, async_get_clientsession(hass))

    data = await client.async_get_extended_data("statussupport_optical")

    assert data == [{"working_temperature_query": "31.05"}]
    request = aioclient_mock.mock_calls[-1]
    assert request[1].query["csrf_token"] == "TESTTOKEN123"  # noqa: S105
    assert request[3]["Accept-Language"] == "en"


async def test_extended_data_fetches_the_token_only_once(hass, aioclient_mock):
    aioclient_mock.get(TOKEN_PAGE, text=STATUS_PAGE_HTML)
    aioclient_mock.get(OPTICAL_PAGE, text="[]", headers={"Content-Type": "text/html"})
    client = Gfm2ApiClient(TEST_IP, async_get_clientsession(hass))

    await client.async_get_extended_data("statussupport_optical")
    await client.async_get_extended_data("statussupport_optical")

    token_requests = [
        call for call in aioclient_mock.mock_calls if call[1].path == "/setup.cgi"
    ]
    assert len(token_requests) == 1


async def test_extended_data_fails_cleanly_without_a_token(hass, aioclient_mock):
    aioclient_mock.get(TOKEN_PAGE, text="<html>no token here</html>")
    client = Gfm2ApiClient(TEST_IP, async_get_clientsession(hass))

    with pytest.raises(Gfm2ApiClientError):
        await client.async_get_extended_data("statussupport_optical")
