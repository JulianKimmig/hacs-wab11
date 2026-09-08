"""Optional-register failures must not masquerade as zero electrical consumption."""

from __future__ import annotations

import pytest
from homeassistant.components.sensor import DATA_COMPONENT
from wab11.exceptions import ConnectionError, ModbusResponseError, TimeoutError

from custom_components.hacs_wab11.diagnostics import async_get_config_entry_diagnostics

PERIODS = ("today", "yesterday", "month", "year")


def modbus_error(code: int) -> ModbusResponseError:
    """Return an external device's input-register exception for integer code."""
    return ModbusResponseError(
        function_code=132, exception_code=code, operation="energy read"
    )


async def test_unsupported_device_loads_legacy_and_recovers_optional_group(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Keep legacy data available and guard optional native access before dereference."""
    fake_system_connection.input_errors[36701] = modbus_error(2)
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data.energy_coordinator
    assert coordinator.last_update_success
    assert coordinator.data.electrical is None
    for period in PERIODS:
        entity_id = f"sensor.wab11_test_electrical_energy_{period}"
        entity = hass.data[DATA_COMPONENT].get_entity(entity_id)
        assert not entity.available
        assert entity.native_value is None
        assert hass.states.get(entity_id).state == "unavailable"
    assert hass.states.get("sensor.wab11_test_total_energy_year").state == "1240.0"
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["energy"]["electrical"] is None

    del fake_system_connection.input_errors[36701]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert (
        hass.states.get("sensor.wab11_test_electrical_energy_yesterday").state == "2.0"
    )
    assert fake_system_connection.input_reads.count((36701, 4)) == 2
    assert fake_system_connection.writes == []


async def test_success_then_unsupported_drops_old_electrical_state(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Publish absence from a successful optional rejection without stale data."""
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data.energy_coordinator
    previous = coordinator.data
    fake_system_connection.input_errors[36701] = modbus_error(2)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert coordinator.data.electrical is None
    assert previous.electrical.year == 316
    assert (
        hass.states.get("sensor.wab11_test_electrical_energy_year").state
        == "unavailable"
    )
    assert hass.states.get("sensor.wab11_test_total_energy_year").state == "1240.0"


@pytest.mark.parametrize(
    "address,error",
    [
        (36701, modbus_error(4)),
        (36701, modbus_error(10)),
        (36701, TimeoutError("timeout")),
        (36701, ConnectionError("offline")),
        (36101, modbus_error(2)),
    ],
)
async def test_failed_energy_coordinator_invalidates_sensors_until_recovery(
    address,
    error,
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Combine optional-data presence with coordinator success to hide stale readings."""
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data.energy_coordinator
    fake_system_connection.input_errors[address] = error
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert entry.runtime_data.runtime.client.energy.electrical is None
    for period in PERIODS:
        assert (
            hass.states.get(f"sensor.wab11_test_electrical_energy_{period}").state
            == "unavailable"
        )
    assert hass.states.get("sensor.wab11_test_total_energy_year").state == "unavailable"
    assert hass.states.get("sensor.wab11_test_outdoor_temperature").state == "4.5"

    del fake_system_connection.input_errors[address]
    fake_system_connection.input_blocks[36701] = [0, 0, 0, 0]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    for period in PERIODS:
        assert (
            hass.states.get(f"sensor.wab11_test_electrical_energy_{period}").state
            == "0.0"
        )
    assert hass.states.get("sensor.wab11_test_total_energy_year").state == "1240.0"


async def test_estimated_power_still_uses_legacy_total(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
    fake_system_connection,
) -> None:
    """Electrical changes alone must not create a new legacy power estimate."""
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    fake_system_connection.input_blocks[36701] = [100, 2, 110, 416]
    await entry.runtime_data.energy_coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.wab11_test_electrical_energy_today").state == "100.0"
    assert (
        hass.states.get("sensor.wab11_test_estimated_total_power").state
        == "unavailable"
    )
    assert hass.states.get("sensor.wab11_test_total_energy_today").state == "12.0"
