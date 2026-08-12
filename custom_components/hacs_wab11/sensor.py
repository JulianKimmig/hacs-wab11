"""Sensor platform for the WAB11 integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENABLE_ADVANCED_SENSORS, CONF_ENABLE_ENERGY_SENSORS
from .coordinator import Wab11RuntimeData
from .entity import Wab11CoordinatorEntity
from .sensor_circuit_descriptions import heating_circuit_sensors
from .sensor_descriptions import (
    ENERGY_SENSORS,
    HEAT_PUMP_SENSORS,
    HOT_WATER_SENSORS,
    SECONDARY_HEAT_SENSORS,
    SYSTEM_SENSORS,
    Wab11SensorDescription,
)


def _enum_name(value: Any) -> str | None:
    if value is None:
        return None
    return value.name.lower()


def _code_or_none(value: int) -> int | None:
    return None if value == 65535 else value


class Wab11Sensor(Wab11CoordinatorEntity, SensorEntity):
    """Generic WAB11 sensor entity."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        runtime_data: Wab11RuntimeData,
        *,
        key: str,
        name: str,
        value_fn: Callable[[Any], Any],
        device_class: SensorDeviceClass | None = None,
        native_unit: str | None = None,
        options: list[str] | None = None,
        state_class: SensorStateClass | None = None,
        enabled_default: bool = True,
    ) -> None:
        super().__init__(coordinator, entry, runtime_data, key, name)
        self._value_fn = value_fn
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = native_unit
        self._attr_options = options
        self._attr_state_class = state_class
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def native_value(self) -> Any:
        return self._value_fn(self.coordinator.data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAB11 sensors from a config entry."""
    runtime_data = entry.runtime_data
    main = runtime_data.main_coordinator
    energy = runtime_data.energy_coordinator
    options = entry.options

    entities: list[Wab11Sensor] = [
        Wab11Sensor(
            main,
            entry,
            runtime_data,
            key="outdoor_temperature",
            name="Outdoor temperature",
            value_fn=lambda data: data.system.outdoor_temp,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit=UnitOfTemperature.CELSIUS,
        ),
        Wab11Sensor(
            main,
            entry,
            runtime_data,
            key="operating_state",
            name="Operating state",
            value_fn=lambda data: _enum_name(data.system.operating_state),
            device_class=SensorDeviceClass.ENUM,
            options=[
                "undefined",
                "relay_test",
                "emergency_off",
                "diagnostics",
                "manual",
                "manual_heating",
                "manual_cooling",
                "manual_defrost",
                "defrost",
                "second_heat_source",
                "evu_lock",
                "sg_tariff",
                "sg_maximum",
                "tariff_charging",
                "elevated_operation",
                "idle_time",
                "standby",
                "flush",
                "frost_protection",
                "heating",
                "hot_water",
                "legionella_protection",
                "heating_cooling_switch",
                "cooling",
                "passive_cooling",
                "summer",
                "pool",
                "vacation",
                "screed",
                "locked",
                "at_lock",
                "summer_lock",
                "winter_lock",
                "operating_limit",
                "hk_lock",
                "setback",
            ],
        ),
        Wab11Sensor(
            main,
            entry,
            runtime_data,
            key="error_code",
            name="Error code",
            value_fn=lambda data: _code_or_none(data.system.error_code),
        ),
        Wab11Sensor(
            main,
            entry,
            runtime_data,
            key="warning_code",
            name="Warning code",
            value_fn=lambda data: _code_or_none(data.system.warning_code),
            enabled_default=False,
        ),
        Wab11Sensor(
            main,
            entry,
            runtime_data,
            key="hot_water_temperature",
            name="Hot water temperature",
            value_fn=lambda data: data.hot_water.current_temp,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit=UnitOfTemperature.CELSIUS,
        ),
        Wab11Sensor(
            main,
            entry,
            runtime_data,
            key="sg_ready_state",
            name="SG-Ready state",
            value_fn=lambda data: _enum_name(data.inputs.sg_ready_state),
            device_class=SensorDeviceClass.ENUM,
            options=["normal", "evu_lock", "recommended", "maximum"],
        ),
    ]

    descriptions = list(SYSTEM_SENSORS)
    for circuit in main.data.heating_circuits:
        if circuit.is_configured:
            descriptions.extend(heating_circuit_sensors(circuit.circuit_id))
    descriptions.extend(HOT_WATER_SENSORS)
    descriptions.extend(SECONDARY_HEAT_SENSORS)
    if options.get(CONF_ENABLE_ADVANCED_SENSORS, False):
        descriptions.extend(HEAT_PUMP_SENSORS)
        descriptions.extend(_legacy_heat_pump_temperature_descriptions())
    if options.get(CONF_ENABLE_ENERGY_SENSORS, True):
        descriptions.extend(ENERGY_SENSORS)

    entities.extend(
        _sensor_from_description(description, main, energy, entry, runtime_data)
        for description in descriptions
    )

    async_add_entities(entities)


def _sensor_from_description(
    description: Wab11SensorDescription,
    main,
    energy,
    entry: ConfigEntry,
    runtime_data: Wab11RuntimeData,
) -> Wab11Sensor:
    """Create an entity from a declarative sensor description."""
    coordinator = energy if description.source == "energy" else main
    return Wab11Sensor(
        coordinator,
        entry,
        runtime_data,
        key=description.key,
        name=description.name,
        value_fn=description.value,
        device_class=description.device_class,
        native_unit=description.native_unit,
        state_class=description.state_class,
        enabled_default=description.enabled_default,
    )


def _legacy_heat_pump_temperature_descriptions() -> tuple[Wab11SensorDescription, ...]:
    """Return existing heat-pump sensor identities for compatibility."""
    return tuple(
        Wab11SensorDescription(
            key=f"heat_pump_{key}_temperature",
            name=f"Heat pump {name} temperature",
            path=f"heat_pump.{path}",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit=UnitOfTemperature.CELSIUS,
            temperature=True,
        )
        for key, name, path in (
            ("flow", "flow", "flow_temp_b4"),
            ("return", "return", "return_temp"),
            ("buffer", "buffer", "buffer_temp_b11"),
            ("separator", "separator", "separator_temp_b2"),
        )
    )
