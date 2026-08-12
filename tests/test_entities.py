"""Behavioral tests for WAB11 entities and write operations."""

from __future__ import annotations

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.number import SERVICE_SET_VALUE
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.components.sensor import DATA_COMPONENT as SENSOR_COMPONENT
from homeassistant.const import ATTR_ENTITY_ID
from wab11.registers.definitions import ALL_REGISTERS
from wab11.registers.formats import FormatCodec

from custom_components.hacs_wab11.const import (
    CONF_ENABLE_ADVANCED_SENSORS,
    CONF_ENABLE_ENERGY_SENSORS,
    CONF_ENABLE_WRITE_ENTITIES,
)
from custom_components.hacs_wab11.sensor import _enum_name


def test_missing_enum_state_is_unavailable() -> None:
    """Represent a missing enum value as an unavailable entity state.

    Returns:
        None.
    """
    assert _enum_name(None) is None


async def test_entities_expose_state_from_library_models(
    hass,
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

    assert hass.states.get("sensor.wab11_test_outdoor_temperature").state == "4.5"
    assert hass.states.get("sensor.wab11_test_operating_state").state == "heating"
    assert hass.states.get("sensor.wab11_test_hot_water_temperature").state == "48.7"
    assert hass.states.get("sensor.wab11_test_sg_ready_state").state == "recommended"
    assert hass.states.get("sensor.wab11_test_total_energy_today").state == "12.0"
    assert hass.states.get("sensor.wab11_test_total_energy_year").state == "1240.0"
    assert hass.states.get("sensor.wab11_test_outdoor_temperature_2").state == "4.2"
    assert hass.states.get("sensor.wab11_test_hk1_room_temperature").state == "20.8"
    assert hass.states.get("sensor.wab11_test_hk2_flow_temperature").state == "29.6"
    assert (
        hass.states.get("sensor.wab11_test_hot_water_effective_setpoint").state
        == "50.0"
    )
    assert hass.states.get("sensor.wab11_test_heat_pump_power_request").state == "47"
    assert (
        hass.states.get("sensor.wab11_test_second_heat_source_operating_hours").state
        == "1200"
    )
    assert (
        hass.states.get("sensor.wab11_test_bivalence_temperature_heating").state
        == "-5.0"
    )
    assert hass.states.get("sensor.wab11_test_heating_energy_yesterday").state == "8.0"
    assert hass.states.get("binary_sensor.wab11_test_input_h1_2").state == "on"
    assert hass.states.get("binary_sensor.wab11_test_heat_pump_running").state == "on"
    assert hass.states.get("binary_sensor.wab11_test_hot_water_charging") is None
    assert (
        hass.states.get("sensor.wab11_test_heat_pump_flow_temperature").state == "33.2"
    )
    assert hass.states.get("binary_sensor.wab11_test_has_error").state == "off"
    assert (
        hass.states.get("binary_sensor.wab11_test_secondary_heat_active").state == "off"
    )
    assert hass.states.get("select.wab11_test_system_mode").state == "heating"
    assert hass.states.get("select.wab11_test_hk1_mode").state == "automatic"
    assert hass.states.get("select.wab11_test_hk2_mode").state == "normal"
    assert hass.states.get("number.wab11_test_hk1_comfort_setpoint").state == "22.5"
    assert (
        hass.states.get("number.wab11_test_hot_water_normal_setpoint").state == "50.0"
    )
    assert hass.states.get("number.wab11_test_hot_water_push_minutes").state == "0.0"
    assert hass.states.get("button.wab11_test_trigger_hot_water_push") is not None
    assert hass.states.get("button.wab11_test_cancel_hot_water_push") is not None
    assert hass.states.get("select.wab11_test_hk3_mode") is None

    sensor_component = hass.data[SENSOR_COMPONENT]
    outdoor = sensor_component.get_entity("sensor.wab11_test_outdoor_temperature")
    room = sensor_component.get_entity("sensor.wab11_test_hk1_room_temperature")
    energy = sensor_component.get_entity("sensor.wab11_test_total_energy_today")
    setpoint = sensor_component.get_entity(
        "sensor.wab11_test_hot_water_effective_setpoint"
    )
    assert outdoor is not None and outdoor.force_update
    assert room is not None and room.force_update
    assert energy is not None and not energy.force_update
    assert setpoint is not None and not setpoint.force_update


async def test_write_entities_call_through_to_the_library(
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

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.wab11_test_system_mode",
            "option": "summer",
        },
        blocking=True,
    )
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.wab11_test_hk1_mode",
            "option": "comfort",
        },
        blocking=True,
    )
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: "number.wab11_test_hk1_comfort_setpoint",
            "value": 21.5,
        },
        blocking=True,
    )
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: "number.wab11_test_hot_water_push_minutes",
            "value": 45,
        },
        blocking=True,
    )
    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {
            ATTR_ENTITY_ID: "button.wab11_test_cancel_hot_water_push",
        },
        blocking=True,
    )

    assert hass.states.get("select.wab11_test_system_mode").state == "summer"
    assert hass.states.get("select.wab11_test_hk1_mode").state == "comfort"
    assert hass.states.get("number.wab11_test_hk1_comfort_setpoint").state == "21.5"
    assert hass.states.get("number.wab11_test_hot_water_push_minutes").state == "0.0"

    expected_writes = [
        (
            ALL_REGISTERS["system_mode"].address,
            FormatCodec.encode(ALL_REGISTERS["system_mode"].fmt, 3),
        ),
        (
            ALL_REGISTERS["hk1_mode"].address,
            FormatCodec.encode(ALL_REGISTERS["hk1_mode"].fmt, 1),
        ),
        (
            ALL_REGISTERS["hk1_setpoint_comfort"].address,
            FormatCodec.encode(ALL_REGISTERS["hk1_setpoint_comfort"].fmt, 21.5),
        ),
        (
            ALL_REGISTERS["ww_push_minutes"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_push_minutes"].fmt, 45),
        ),
        (
            ALL_REGISTERS["ww_push_minutes"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_push_minutes"].fmt, 0),
        ),
    ]

    assert fake_system_connection.writes[-5:] == expected_writes


async def test_additional_write_entities_respect_library_rate_limits(
    hass,
    fake_system_connection,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    """Exercise remaining write entities below the device safety threshold.

    Args:
        hass: Home Assistant test instance.
        fake_system_connection: External Modbus test double.
        integration_data: Valid baseline config-entry data.
        integration_options: Valid baseline integration options.
        make_mock_config_entry: Factory for Home Assistant config entries.

    Returns:
        None.
    """
    options = {**integration_options, CONF_ENABLE_WRITE_ENTITIES: True}
    entry = make_mock_config_entry(integration_data, options=options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for entity_id, value in (
        ("number.wab11_test_hk1_normal_setpoint", 20.5),
        ("number.wab11_test_hk1_setback_setpoint", 17.5),
        ("number.wab11_test_hot_water_normal_setpoint", 52.0),
        ("number.wab11_test_hot_water_setback_setpoint", 42.0),
    ):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, "value": value},
            blocking=True,
        )
    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {ATTR_ENTITY_ID: "button.wab11_test_trigger_hot_water_push"},
        blocking=True,
    )

    assert hass.states.get("number.wab11_test_hk1_normal_setpoint").state == "20.5"
    assert hass.states.get("number.wab11_test_hk1_setback_setpoint").state == "17.5"
    assert (
        hass.states.get("number.wab11_test_hot_water_normal_setpoint").state == "52.0"
    )
    assert (
        hass.states.get("number.wab11_test_hot_water_setback_setpoint").state == "42.0"
    )
    assert fake_system_connection.writes[-5:] == [
        (
            ALL_REGISTERS["hk1_setpoint_normal"].address,
            FormatCodec.encode(ALL_REGISTERS["hk1_setpoint_normal"].fmt, 20.5),
        ),
        (
            ALL_REGISTERS["hk1_setpoint_setback"].address,
            FormatCodec.encode(ALL_REGISTERS["hk1_setpoint_setback"].fmt, 17.5),
        ),
        (
            ALL_REGISTERS["ww_normal"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_normal"].fmt, 52.0),
        ),
        (
            ALL_REGISTERS["ww_setback"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_setback"].fmt, 42.0),
        ),
        (
            ALL_REGISTERS["ww_push_minutes"].address,
            FormatCodec.encode(ALL_REGISTERS["ww_push_minutes"].fmt, 30),
        ),
    ]
