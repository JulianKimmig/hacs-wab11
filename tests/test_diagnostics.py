from __future__ import annotations

from custom_components.hacs_wab11.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_redacts_connection_details(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["host"] == "**REDACTED**"
    assert diagnostics["entry"]["port"] == "**REDACTED**"
    assert diagnostics["entry"]["unit_id"] == "**REDACTED**"
    assert diagnostics["main"]["system"]["outdoor_temp_1"] == 4.5
    assert diagnostics["main"]["system"]["system_mode"] == "HEATING"
    assert diagnostics["energy"]["total"]["year"] == 1240
