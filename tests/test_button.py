"""Tests for the restart button."""


async def test_restart_button_triggers_reboot(hass, config_entry, mock_api):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.glasfaser_modem_2_restart"},
        blocking=True,
    )
    mock_api["do_reboot"].assert_called_once()
