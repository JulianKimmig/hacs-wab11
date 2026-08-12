"""Behavioral tests for WAB11 service actions."""

from __future__ import annotations

import pytest
from homeassistant.exceptions import HomeAssistantError
from wab11.models.heating import PartyPauseCode
from wab11.registers.definitions import ALL_REGISTERS
from wab11.registers.formats import FormatCodec

from custom_components.hacs_wab11 import async_setup
from custom_components.hacs_wab11.const import (
    ATTR_CIRCUIT,
    ATTR_ENTRY_ID,
    ATTR_HOURS,
    ATTR_MINUTES,
    ATTR_MODE,
    CONF_ENABLE_WRITE_ENTITIES,
    SERVICE_CANCEL_HOT_WATER_PUSH,
    SERVICE_CANCEL_PARTY_PAUSE,
    SERVICE_SET_PARTY_PAUSE,
    SERVICE_TRIGGER_HOT_WATER_PUSH,
)


async def test_custom_services_call_curated_write_operations(
    hass,
    fake_system_connection,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    options = {
        **integration_options,
        CONF_ENABLE_WRITE_ENTITIES: True,
    }
    entry = make_mock_config_entry(integration_data, options=options)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "hacs_wab11",
        SERVICE_SET_PARTY_PAUSE,
        {
            ATTR_ENTRY_ID: entry.entry_id,
            ATTR_CIRCUIT: 1,
            ATTR_MODE: "party",
            ATTR_HOURS: 2.5,
        },
        blocking=True,
    )
    await hass.services.async_call(
        "hacs_wab11",
        SERVICE_CANCEL_PARTY_PAUSE,
        {
            ATTR_ENTRY_ID: entry.entry_id,
            ATTR_CIRCUIT: 1,
        },
        blocking=True,
    )
    await hass.services.async_call(
        "hacs_wab11",
        SERVICE_TRIGGER_HOT_WATER_PUSH,
        {
            ATTR_MINUTES: 35,
        },
        blocking=True,
    )
    await hass.services.async_call(
        "hacs_wab11",
        SERVICE_CANCEL_HOT_WATER_PUSH,
        {
            ATTR_ENTRY_ID: entry.entry_id,
        },
        blocking=True,
    )

    expected_writes = [
        (
            ALL_REGISTERS["hk1_party_pause"].address,
            FormatCodec.encode(
                ALL_REGISTERS["hk1_party_pause"].fmt,
                PartyPauseCode.party_hours(2.5),
            ),
        ),
        (
            ALL_REGISTERS["hk1_party_pause"].address,
            FormatCodec.encode(
                ALL_REGISTERS["hk1_party_pause"].fmt,
                PartyPauseCode.AUTOMATIC,
            ),
        ),
        (
            ALL_REGISTERS["ww_push_minutes"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_push_minutes"].fmt, 35),
        ),
        (
            ALL_REGISTERS["ww_push_minutes"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_push_minutes"].fmt, 0),
        ),
    ]

    assert fake_system_connection.writes[-4:] == expected_writes
    assert hass.states.get("number.wab11_test_hot_water_push_minutes").state == "0.0"


async def test_custom_services_reject_writes_when_write_entities_are_disabled(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    entry = make_mock_config_entry(
        integration_data,
        options={**integration_options, CONF_ENABLE_WRITE_ENTITIES: False},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match="Write entities are disabled"):
        await hass.services.async_call(
            "hacs_wab11",
            SERVICE_TRIGGER_HOT_WATER_PUSH,
            {
                ATTR_ENTRY_ID: entry.entry_id,
                ATTR_MINUTES: 30,
            },
            blocking=True,
        )


async def test_custom_services_require_a_loaded_target(
    hass,
) -> None:
    """Reject service actions when no WAB11 config entry is loaded.

    Args:
        hass: Home Assistant test instance.

    Returns:
        None.
    """
    assert await async_setup(hass, {})

    with pytest.raises(HomeAssistantError, match="No WAB11 integrations are loaded"):
        await hass.services.async_call(
            "hacs_wab11",
            SERVICE_CANCEL_HOT_WATER_PUSH,
            blocking=True,
        )


async def test_custom_services_validate_entry_selection(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    """Require an existing entry ID when multiple entries are loaded.

    Args:
        hass: Home Assistant test instance.
        integration_data: Valid baseline config-entry data.
        integration_options: Valid baseline integration options.
        make_mock_config_entry: Factory for Home Assistant config entries.

    Returns:
        None.
    """
    first = make_mock_config_entry(integration_data, options=integration_options)
    second_data = {**integration_data, "host": "192.0.2.16"}
    second = make_mock_config_entry(second_data, options=integration_options)
    first.add_to_hass(hass)
    assert await hass.config_entries.async_setup(first.entry_id)
    second.add_to_hass(hass)
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match="entry_id is required"):
        await hass.services.async_call(
            "hacs_wab11",
            SERVICE_CANCEL_HOT_WATER_PUSH,
            blocking=True,
        )

    with pytest.raises(HomeAssistantError, match="Unknown WAB11 entry_id"):
        await hass.services.async_call(
            "hacs_wab11",
            SERVICE_CANCEL_HOT_WATER_PUSH,
            {ATTR_ENTRY_ID: "missing-entry"},
            blocking=True,
        )
