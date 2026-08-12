"""Sensor descriptions for the complete WAB11 state surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)


@dataclass(frozen=True, kw_only=True)
class Wab11SensorDescription:
    """Describe one value exposed as a Home Assistant sensor.

    Attributes:
        key: Stable suffix used in the entity unique ID.
        name: Human-readable entity name.
        path: Attribute path below coordinator data.
        source: Coordinator source, either ``main`` or ``energy``.
        device_class: Optional Home Assistant sensor device class.
        native_unit: Optional native unit of measurement.
        state_class: Optional long-term-statistics state class.
        enum: Whether the resolved value is represented by an enum name.
        temperature: Whether the resolved value is a library Temperature.
        enabled_default: Whether the entity is enabled by default.
    """

    key: str
    name: str
    path: str
    source: str = "main"
    device_class: SensorDeviceClass | None = None
    native_unit: str | None = None
    state_class: SensorStateClass | None = None
    enum: bool = False
    temperature: bool = False
    enabled_default: bool = True

    def value(self, data: Any) -> Any:
        """Resolve and normalize this value from coordinator data.

        Args:
            data: Main or energy coordinator data object.

        Returns:
            A Home Assistant-compatible native state value.
        """
        value = data
        for part in self.path.split("."):
            value = value[int(part)] if part.isdigit() else getattr(value, part)
        if self.temperature:
            return value.celsius
        if self.enum:
            return value.name.lower()
        return value


TEMP = {
    "device_class": SensorDeviceClass.TEMPERATURE,
    "native_unit": UnitOfTemperature.CELSIUS,
    "temperature": True,
}
PERCENT = {"native_unit": PERCENTAGE}


SYSTEM_SENSORS = (
    Wab11SensorDescription(
        key="outdoor_temperature_2",
        name="Outdoor temperature 2",
        path="system.outdoor_temp_2",
        **TEMP,
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
        **PERCENT,
    ),
    Wab11SensorDescription(
        key="heat_pump_evaporator_temperature",
        name="Heat pump evaporator temperature",
        path="heat_pump.evaporator_temp",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_suction_gas_temperature",
        name="Heat pump suction gas temperature",
        path="heat_pump.suction_gas_temp",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_regenerative_flow_temperature",
        name="Heat pump regenerative flow temperature",
        path="heat_pump.regenerative_flow_b21",
        **TEMP,
    ),
    Wab11SensorDescription(
        key="heat_pump_sum_flow_temperature",
        name="Heat pump sum flow temperature",
        path="heat_pump.sum_flow_b7",
        **TEMP,
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

ENERGY_SENSORS = tuple(
    Wab11SensorDescription(
        key=f"{category}_energy_{period}",
        name=f"{category.replace('_', ' ').title()} energy {period}",
        path=f"{category}.{period}",
        source="energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )
    for category in ("total", "heating", "hot_water", "cooling")
    for period in ("today", "yesterday", "month", "year")
)
