"""Tests for diagnostics output."""

from custom_components.gfm2.diagnostics import async_get_config_entry_diagnostics

from .conftest import TEST_IP, TEST_SERIAL


async def test_diagnostics_redact_serial_number(hass, config_entry, mock_api):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, config_entry)

    assert result["entry_data"]["ip_address"] == TEST_IP
    assert result["data"]["status_serial_number"] == "**REDACTED**"
    assert TEST_SERIAL not in str(result)
    assert result["data"]["status_txpower"] == 2.39
