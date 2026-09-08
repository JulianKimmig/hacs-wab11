"""Sensor descriptions for the complete WAB11 state surface."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)

from . import sensor_energy_descriptions
from .sensor_description import Wab11SensorDescription

ENERGY_SENSORS = sensor_energy_descriptions.ENERGY_SENSORS

TEMP = {
    "device_class": SensorDeviceClass.TEMPERATURE,
    "native_unit": UnitOfTemperature.CELSIUS,
    "temperature": True,
}
MEASURED_TEMP = {**TEMP, "force_update": True}
PERCENT = {"native_unit": PERCENTAGE}
MEASURED_PERCENT = {**PERCENT, "force_update": True}


SYSTEM_SENSORS = (
    Wab11SensorDescription(
        key="outdoor_temperature_2",
        name="Outdoor temperature 2",
        path="system.outdoor_temp_2",
        **MEASURED_TEMP,
    ),
    Wab11SensorDescription(
        key="power_request",
        name="System power request",
        path="system.power_request_watts",
        device_class=SensorDeviceClass.POWER,
        native_unit=UnitOfPower.WATT,
    ),
)

HOT_WATER_SENSORS = (
    Wab11SensorDescription(
        key="hot_water_config",
        name="Hot water configuration",
        path="hot_water.config",
        enum=True,
        enabled_default=False,
    ),
    Wab11SensorDescription(
        key="hot_water_effective_setpoint",
        name="Hot water effective setpoint",
        path="hot_water.setpoint_effective",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="hot_water_sg_ready_boost",
        name="Hot water SG-Ready boost",
        path="hot_water.sg_ready_boost",
        native_unit=UnitOfTemperature.KELVIN,
        temperature=True,
    ),
    Wab11SensorDescription(
        key="hot_water_temperature_difference",
        name="Hot water temperature difference",
        path="hot_water.temp_difference",
        native_unit=UnitOfTemperature.KELVIN,
    ),
)

HEAT_PUMP_SENSORS = (
    Wab11SensorDescription(
        key="heat_pump_config",
        name="Heat pump configuration",
        path="heat_pump.config",
        enum=True,
        enabled_default=False,
    ),
    Wab11SensorDescription(
        key="heat_pump_operating_state",
        name="Heat pump operating state",
        path="heat_pump.operating_state",
        enum=True,
    ),
    Wab11SensorDescription(
        key="heat_pump_power_request",
        name="Heat pump power request",
        path="heat_pump.power_request_percent",
        **MEASURED_PERCENT,
    ),
    Wab11SensorDescription(
        key="heat_pump_evaporator_temperature",
        name="Heat pump evaporator temperature",
        path="heat_pump.evaporator_temp",
        **MEASURED_TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_suction_gas_temperature",
        name="Heat pump suction gas temperature",
        path="heat_pump.suction_gas_temp",
        **MEASURED_TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_regenerative_flow_temperature",
        name="Heat pump regenerative flow temperature",
        path="heat_pump.regenerative_flow_b21",
        **MEASURED_TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_sum_flow_temperature",
        name="Heat pump sum flow temperature",
        path="heat_pump.sum_flow_b7",
        **MEASURED_TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_temperature_spread",
        name="Heat pump temperature spread",
        path="heat_pump.spread",
        native_unit=UnitOfTemperature.KELVIN,
    ),
    Wab11SensorDescription(
        key="heat_pump_quiet_mode",
        name="Heat pump quiet mode setting",
        path="heat_pump.quiet_mode",
        enabled_default=False,
    ),
    Wab11SensorDescription(
        key="heat_pump_start_mode",
        name="Heat pump start mode",
        path="heat_pump.pump_start_mode",
        enabled_default=False,
    ),
    *(
        Wab11SensorDescription(
            key=f"heat_pump_power_{mode}",
            name=f"Heat pump power {mode.replace('_', ' ')}",
            path=f"heat_pump.pump_power_{mode}",
            **PERCENT,
        )
        for mode in ("heating", "cooling", "hot_water", "defrost")
    ),
    *(
        Wab11SensorDescription(
            key=f"heat_pump_flow_rate_{mode}",
            name=f"Heat pump flow rate {mode.replace('_', ' ')}",
            path=f"heat_pump.flow_rate_{mode}",
            enabled_default=False,
        )
        for mode in ("heating", "cooling", "hot_water")
    ),
)

SECONDARY_HEAT_SENSORS = (
    Wab11SensorDescription(
        key="wez2_status",
        name="Second heat source status",
        path="secondary_heat.status_wez2",
    ),
    Wab11SensorDescription(
        key="wez2_operating_hours",
        name="Second heat source operating hours",
        path="secondary_heat.operating_hours_wez2",
        device_class=SensorDeviceClass.DURATION,
        native_unit=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    Wab11SensorDescription(
        key="wez2_switching_cycles",
        name="Second heat source switching cycles",
        path="secondary_heat.switching_cycles_wez2",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    Wab11SensorDescription(
        key="e1_operating_hours",
        name="Electric heater 1 operating hours",
        path="secondary_heat.operating_hours_e1",
        device_class=SensorDeviceClass.DURATION,
        native_unit=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    Wab11SensorDescription(
        key="e2_operating_hours",
        name="Electric heater 2 operating hours",
        path="secondary_heat.operating_hours_e2",
        device_class=SensorDeviceClass.DURATION,
        native_unit=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    *(
        Wab11SensorDescription(
            key=key, name=name, path=f"secondary_heat.{key}", enabled_default=False
        )
        for key, name in (
            ("config_wez2", "Second heat source configuration"),
            ("config_e1", "Electric heater 1 configuration"),
            ("config_e2", "Electric heater 2 configuration"),
        )
    ),
    Wab11SensorDescription(
        key="secondary_heat_limit_temperature",
        name="Secondary heat limit temperature",
        path="secondary_heat.limit_temp",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="bivalence_temperature_heating",
        name="Bivalence temperature heating",
        path="secondary_heat.bivalence_temp_heating",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="bivalence_temperature_hot_water",
        name="Bivalence temperature hot water",
        path="secondary_heat.bivalence_temp_hot_water",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="secondary_heat_total_operating_hours",
        name="Secondary heat total operating hours",
        path="secondary_heat.total_operating_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)
