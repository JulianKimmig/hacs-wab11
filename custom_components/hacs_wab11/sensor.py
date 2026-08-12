"""Sensor platform for the WAB11 integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENABLE_ADVANCED_SENSORS, CONF_ENABLE_ENERGY_SENSORS
from .coordinator import Wab11RuntimeData
from .entity import Wab11CoordinatorEntity


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
        enabled_default: bool = True,
    ) -> None:
        super().__init__(coordinator, entry, runtime_data, key, name)
        self._value_fn = value_fn
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = native_unit
        self._attr_options = options
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

    if options.get(CONF_ENABLE_ADVANCED_SENSORS, False):
        entities.extend(
            [
                Wab11Sensor(
                    main,
                    entry,
                    runtime_data,
                    key="heat_pump_flow_temperature",
                    name="Heat pump flow temperature",
                    value_fn=lambda data: data.heat_pump.flow_temp_b4.celsius,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
                Wab11Sensor(
                    main,
                    entry,
                    runtime_data,
                    key="heat_pump_return_temperature",
                    name="Heat pump return temperature",
                    value_fn=lambda data: data.heat_pump.return_temp.celsius,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
                Wab11Sensor(
                    main,
                    entry,
                    runtime_data,
                    key="heat_pump_buffer_temperature",
                    name="Heat pump buffer temperature",
                    value_fn=lambda data: data.heat_pump.buffer_temp_b11.celsius,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
                Wab11Sensor(
                    main,
                    entry,
                    runtime_data,
                    key="heat_pump_separator_temperature",
                    name="Heat pump separator temperature",
                    value_fn=lambda data: data.heat_pump.separator_temp_b2.celsius,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
            ]
        )

    if options.get(CONF_ENABLE_ENERGY_SENSORS, True):
        entities.extend(
            [
                Wab11Sensor(
                    energy,
                    entry,
                    runtime_data,
                    key="total_energy_today",
                    name="Total energy today",
                    value_fn=lambda data: data.total.today,
                    device_class=SensorDeviceClass.ENERGY,
                    native_unit=UnitOfEnergy.KILO_WATT_HOUR,
                ),
                Wab11Sensor(
                    energy,
                    entry,
                    runtime_data,
                    key="total_energy_month",
                    name="Total energy month",
                    value_fn=lambda data: data.total.month,
                    device_class=SensorDeviceClass.ENERGY,
                    native_unit=UnitOfEnergy.KILO_WATT_HOUR,
                ),
                Wab11Sensor(
                    energy,
                    entry,
                    runtime_data,
                    key="total_energy_year",
                    name="Total energy year",
                    value_fn=lambda data: data.total.year,
                    device_class=SensorDeviceClass.ENERGY,
                    native_unit=UnitOfEnergy.KILO_WATT_HOUR,
                ),
            ]
        )

    async_add_entities(entities)
