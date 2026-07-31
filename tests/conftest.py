"""Fixtures for the GFM2 test suite."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_IP_ADDRESS
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gfm2.const import DOMAIN

FIXTURES = Path(__file__).parent / "fixtures"

TEST_IP = "192.168.100.1"
TEST_SERIAL = "53434F4D00C0FFEE"


def load_json_fixture(name: str) -> object:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    return


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a mock config entry matching an existing installation."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=TEST_IP,
        data={CONF_IP_ADDRESS: TEST_IP},
    )


@pytest.fixture
def mock_api():
    """Patch the API client to serve recorded fixture data."""
    with (
        patch(
            "custom_components.gfm2.api.Gfm2ApiClient.async_get_status_data",
            return_value=load_json_fixture("status_full.json"),
        ) as status_mock,
        patch(
            "custom_components.gfm2.api.Gfm2ApiClient.async_get_firmware_data",
            return_value=load_json_fixture("firmware.json"),
        ) as firmware_mock,
        patch(
            "custom_components.gfm2.api.Gfm2ApiClient.async_get_reboot_data",
            return_value=load_json_fixture("reboot.json"),
        ) as reboot_mock,
        patch(
            "custom_components.gfm2.api.Gfm2ApiClient.async_do_reboot",
            return_value=None,
        ) as do_reboot_mock,
    ):
        yield {
            "status": status_mock,
            "firmware": firmware_mock,
            "reboot": reboot_mock,
            "do_reboot": do_reboot_mock,
        }
