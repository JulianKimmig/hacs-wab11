"""Electrical energy entities retain separate identities and calendar semantics."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.components.sensor import (
    DATA_COMPONENT,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from custom_components.hacs_wab11.const import CONF_ENABLE_ENERGY_SENSORS
from custom_components.hacs_wab11.diagnostics import async_get_config_entry_diagnostics

PERIODS = ("today", "yesterday", "month", "year")


async def test_electrical_entities_expose_separate_values_and_metadata(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Set up real entities and verify values, coordinator, IDs, units and precision."""
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    component = hass.data[DATA_COMPONENT]
    registry = er.async_get(hass)
    coordinator = entry.runtime_data.energy_coordinator
    assert coordinator.update_interval == timedelta(seconds=300)
    for period, value in zip(PERIODS, (0, 2, 10, 316), strict=True):
        key = f"electrical_energy_{period}"
        entity_id = f"sensor.wab11_test_{key}"
        entity = component.get_entity(entity_id)
        state = hass.states.get(entity_id)
        assert state is not None
        assert float(state.state) == value
        assert entity.native_value == value
        assert entity.available
        assert entity.coordinator is coordinator
        assert entity.device_class is SensorDeviceClass.ENERGY
        assert entity.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
        assert entity.suggested_display_precision == 0
        assert not entity.force_update
        expected_class = (
            None if period == "yesterday" else SensorStateClass.TOTAL_INCREASING
        )
        assert entity.state_class is expected_class
        assert registry.async_get(entity_id).unique_id == f"{entry.unique_id}_{key}"

    for category, values in {
        "total": (12, 11, 210, 1240),
        "heating": (9, 8, 150, 900),
        "hot_water": (3, 3, 60, 280),
        "cooling": (0, 0, 0, 0),
    }.items():
        for period, value in zip(PERIODS, values, strict=True):
            entity_id = f"sensor.wab11_test_{category}_energy_{period}"
            assert float(hass.states.get(entity_id).state) == value
            assert (
                registry.async_get(entity_id).unique_id
                == f"{entry.unique_id}_{category}_energy_{period}"
            )
    assert fake_system_connection.input_reads.count((36701, 4)) == 1
    assert fake_system_connection.writes == []

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["energy"]["electrical"] == {
        "today": 0.0,
        "yesterday": 2.0,
        "month": 10.0,
        "year": 316.0,
    }
    assert diagnostics["energy"]["total"]["year"] == 1240


async def test_disabling_energy_option_omits_all_electrical_entities(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    """Apply the existing energy option without adding a second option or coordinator."""
    entry = make_mock_config_entry(
        integration_data,
        options={
            **integration_options,
            CONF_ENABLE_ENERGY_SENSORS: False,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    for period in PERIODS:
        entity_id = f"sensor.wab11_test_electrical_energy_{period}"
        assert hass.states.get(entity_id) is None
        assert registry.async_get(entity_id) is None
    assert hass.states.get("sensor.wab11_test_total_energy_today") is None
    assert hass.states.get("sensor.wab11_test_estimated_total_power") is None


@pytest.mark.parametrize("raw", [0, 65535])
async def test_electrical_boundaries_are_available_numeric_values(
    raw,
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Preserve valid all-zero and unsigned-maximum periods without missing sentinels."""
    fake_system_connection.input_blocks[36701] = [raw] * 4
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for period in PERIODS:
        assert (
            float(
                hass.states.get(f"sensor.wab11_test_electrical_energy_{period}").state
            )
            == raw
        )


async def test_calendar_changes_and_unchanged_samples_do_not_force_updates(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Publish period decreases, keep yesterday unaggregated, and omit duplicate events."""
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data.energy_coordinator
    entity_ids = [f"sensor.wab11_test_electrical_energy_{period}" for period in PERIODS]
    changes = []

    def record_change(event):
        """Record actual Home Assistant state-change events for the four entities."""
        changes.append(event)

    unsubscribe = async_track_state_change_event(hass, entity_ids, record_change)
    try:
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert changes == []
        fake_system_connection.input_blocks[36701] = [2, 7, 10, 316]
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        fake_system_connection.input_blocks[36701] = [0, 2, 0, 0]
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        for entity_id, value in zip(entity_ids, (0, 2, 0, 0), strict=True):
            assert float(hass.states.get(entity_id).state) == value
        assert len(changes) == 6
        yesterday = hass.data[DATA_COMPONENT].get_entity(entity_ids[1])
        assert yesterday.state_class is None
    finally:
        unsubscribe()


async def test_electrical_entities_keep_ids_across_reload(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    """Retain registry identities for both legacy and new groups through reload."""
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    identities = {
        entity.entity_id: entity.unique_id
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
    }
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert {
        entity.entity_id: entity.unique_id
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
    } == identities
