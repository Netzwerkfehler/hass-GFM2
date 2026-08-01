"""Tests for sensor states."""

from datetime import UTC, datetime

from homeassistant.util import dt as dt_util


async def test_last_reboot_is_read_as_device_local_time(hass, config_entry, mock_api):
    """
    The device reports local time, so it must not be parsed as UTC.

    The fixture reports "01.07.2026 04:30". In Europe/Berlin that is UTC+2 in
    summer, so the correct instant is 02:30 UTC. Parsing it as UTC instead put
    the timestamp two hours into the future.

    Home Assistant renders timestamp states in UTC, so this compares the
    instant rather than its notation.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.glasfaser_modem_2_last_reboot")
    assert dt_util.parse_datetime(state.state) == datetime(
        2026, 7, 1, 2, 30, tzinfo=UTC
    )
