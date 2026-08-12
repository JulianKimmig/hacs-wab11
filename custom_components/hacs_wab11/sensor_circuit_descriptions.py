"""Heating-circuit sensor descriptions for the WAB11 integration."""

from __future__ import annotations

from homeassistant.const import UnitOfTemperature

from .sensor_descriptions import (
    MEASURED_PERCENT,
    MEASURED_TEMP,
    TEMP,
    Wab11SensorDescription,
)


def heating_circuit_sensors(circuit_id: int) -> tuple[Wab11SensorDescription, ...]:
    """Build descriptions for one configured heating circuit.

    Args:
        circuit_id: One-based heating circuit number.

    Returns:
        Descriptions for circuit values not represented by write entities.
    """
    base = f"heating_circuits.{circuit_id - 1}"
    prefix = f"hk{circuit_id}"
    label = f"HK{circuit_id}"
    return (
        Wab11SensorDescription(
            key=f"{prefix}_config",
            name=f"{label} configuration",
            path=f"{base}.config",
            enum=True,
            enabled_default=False,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_room_effective_setpoint",
            name=f"{label} room effective setpoint",
            path=f"{base}.room_setpoint_effective",
            **TEMP,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_room_temperature",
            name=f"{label} room temperature",
            path=f"{base}.room_temp",
            **MEASURED_TEMP,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_room_humidity",
            name=f"{label} room humidity",
            path=f"{base}.room_humidity",
            **MEASURED_PERCENT,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_flow_setpoint",
            name=f"{label} flow setpoint",
            path=f"{base}.flow_setpoint",
            **TEMP,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_flow_temperature",
            name=f"{label} flow temperature",
            path=f"{base}.flow_temp",
            **MEASURED_TEMP,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_request_type",
            name=f"{label} request type",
            path=f"{base}.request_type",
            enum=True,
            enabled_default=False,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_party_pause",
            name=f"{label} party pause code",
            path=f"{base}.party_pause",
            enabled_default=False,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_heating_curve",
            name=f"{label} heating curve",
            path=f"{base}.heating_curve_slope",
        ),
        Wab11SensorDescription(
            key=f"{prefix}_summer_winter_threshold",
            name=f"{label} summer winter threshold",
            path=f"{base}.summer_winter_threshold",
            native_unit=UnitOfTemperature.CELSIUS,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_constant_temperature_heating",
            name=f"{label} constant temperature heating",
            path=f"{base}.constant_temp_heating",
            **TEMP,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_constant_temperature_heating_setback",
            name=f"{label} constant temperature heating setback",
            path=f"{base}.constant_temp_heating_setback",
            **TEMP,
        ),
        Wab11SensorDescription(
            key=f"{prefix}_constant_temperature_cooling",
            name=f"{label} constant temperature cooling",
            path=f"{base}.constant_temp_cooling",
            **TEMP,
        ),
    )
