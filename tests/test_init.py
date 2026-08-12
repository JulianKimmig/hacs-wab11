"""Lifecycle tests for the WAB11 config entry."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from wab11.exceptions import ConnectionError

from custom_components.hacs_wab11.const import (
    CONF_ENABLE_ADVANCED_SENSORS,
    CONF_ENABLE_ENERGY_SENSORS,
    CONF_ENABLE_WRITE_ENTITIES,
)


async def test_setup_reload_and_unload_entry(
    hass,
    fake_system_connection,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    options = {
        **integration_options,
        CONF_ENABLE_WRITE_ENTITIES: True,
        CONF_ENABLE_ENERGY_SENSORS: True,
        CONF_ENABLE_ADVANCED_SENSORS: True,
    }
    entry = make_mock_config_entry(integration_data, options=options)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime_data = entry.runtime_data
    assert runtime_data.runtime.client.system.outdoor_temp == 4.5
    assert runtime_data.main_coordinator.data is not None
    assert runtime_data.energy_coordinator.data is not None

    entity_registry = er.async_get(hass)
    assert (
        entity_registry.async_get("sensor.wab11_test_outdoor_temperature") is not None
    )
    assert entity_registry.async_get("select.wab11_test_system_mode") is not None
    assert (
        entity_registry.async_get("button.wab11_test_trigger_hot_water_push")
        is not None
    )

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.runtime_data is not runtime_data

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert fake_system_connection.is_connected is False


async def test_read_only_setup_only_loads_read_entities(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    options = {
        **integration_options,
        CONF_ENABLE_WRITE_ENTITIES: False,
        CONF_ENABLE_ENERGY_SENSORS: False,
        CONF_ENABLE_ADVANCED_SENSORS: False,
    }
    entry = make_mock_config_entry(integration_data, options=options)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    states = hass.states.async_all()
    entity_ids = {state.entity_id for state in states}

    assert "sensor.wab11_test_outdoor_temperature" in entity_ids
    assert "binary_sensor.wab11_test_has_error" in entity_ids
    assert "select.wab11_test_system_mode" not in entity_ids
    assert "number.wab11_test_hk1_comfort_setpoint" not in entity_ids
    assert "button.wab11_test_trigger_hot_water_push" not in entity_ids


async def test_setup_retries_and_disconnects_after_device_failure(
    hass,
    fake_system_connection,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    """Fail setup cleanly when the initial controller refresh fails.

    Args:
        hass: Home Assistant test instance.
        fake_system_connection: External Modbus test double.
        integration_data: Valid baseline config-entry data.
        integration_options: Valid baseline integration options.
        make_mock_config_entry: Factory for Home Assistant config entries.

    Returns:
        None.
    """
    fake_system_connection.read_error = ConnectionError("controller offline")
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert fake_system_connection.is_connected is False


async def test_coordinators_translate_runtime_connection_failures(
    hass,
    fake_system_connection,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    """Translate later controller failures into coordinator update failures.

    Args:
        hass: Home Assistant test instance.
        fake_system_connection: External Modbus test double.
        integration_data: Valid baseline config-entry data.
        integration_options: Valid baseline integration options.
        make_mock_config_entry: Factory for Home Assistant config entries.

    Returns:
        None.
    """
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    fake_system_connection.read_error = ConnectionError("controller offline")
    with pytest.raises(UpdateFailed, match="controller offline"):
        await entry.runtime_data.main_coordinator._async_update_data()
    with pytest.raises(UpdateFailed, match="controller offline"):
        await entry.runtime_data.energy_coordinator._async_update_data()
