"""Binary sensor platform for the WAB11 integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import Wab11RuntimeData
from .entity import Wab11CoordinatorEntity


class Wab11BinarySensor(Wab11CoordinatorEntity, BinarySensorEntity):
    """Generic binary sensor for WAB11."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        runtime_data: Wab11RuntimeData,
        *,
        key: str,
        name: str,
        is_on_fn: Callable[[Any], bool],
        device_class: BinarySensorDeviceClass | None = None,
        enabled_default: bool = True,
    ) -> None:
        super().__init__(coordinator, entry, runtime_data, key, name)
        self._is_on_fn = is_on_fn
        self._attr_device_class = device_class
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def is_on(self) -> bool:
        return self._is_on_fn(self.coordinator.data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAB11 binary sensors."""
    runtime_data = entry.runtime_data
    main = runtime_data.main_coordinator
    entities = [
        Wab11BinarySensor(
            main,
            entry,
            runtime_data,
            key="has_error",
            name="Has error",
            is_on_fn=lambda data: data.system.has_error,
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        Wab11BinarySensor(
            main,
            entry,
            runtime_data,
            key="has_warning",
            name="Has warning",
            is_on_fn=lambda data: data.system.has_warning,
            device_class=BinarySensorDeviceClass.PROBLEM,
            enabled_default=False,
        ),
        Wab11BinarySensor(
            main,
            entry,
            runtime_data,
            key="secondary_heat_active",
            name="Secondary heat active",
            is_on_fn=lambda data: data.secondary_heat.any_backup_active,
            device_class=BinarySensorDeviceClass.HEAT,
        ),
    ]

    for key, name, attribute in (
        ("system_heating", "System heating", "is_heating"),
        ("system_cooling", "System cooling", "is_cooling"),
        ("system_hot_water", "System hot water", "is_hot_water"),
        ("system_defrosting", "System defrosting", "is_defrosting"),
        ("system_standby", "System standby", "is_standby"),
    ):
        entities.append(
            Wab11BinarySensor(
                main,
                entry,
                runtime_data,
                key=key,
                name=name,
                is_on_fn=lambda data, attribute=attribute: getattr(
                    data.system, attribute
                ),
                device_class=BinarySensorDeviceClass.RUNNING,
                enabled_default=False,
            )
        )

    for key, name, attribute in (
        ("heat_pump_error_free", "Heat pump error free", "is_error_free"),
        ("heat_pump_running", "Heat pump running", "is_running"),
        ("heat_pump_heating", "Heat pump heating", "is_heating"),
        ("heat_pump_cooling", "Heat pump cooling", "is_cooling"),
        ("heat_pump_defrosting", "Heat pump defrosting", "is_defrosting"),
        ("heat_pump_hot_water", "Heat pump hot water", "is_hot_water"),
        ("heat_pump_quiet", "Heat pump quiet mode", "is_quiet_mode"),
    ):
        entities.append(
            Wab11BinarySensor(
                main,
                entry,
                runtime_data,
                key=key,
                name=name,
                is_on_fn=lambda data, attribute=attribute: getattr(
                    data.heat_pump, attribute
                ),
                device_class=BinarySensorDeviceClass.RUNNING,
                enabled_default=key == "heat_pump_running",
            )
        )

    for key, name, attribute in (
        ("wez2_active", "Second heat source active", "is_wez2_active"),
        ("electric_heater_1", "Electric heater 1 active", "is_e1_active"),
        ("electric_heater_2", "Electric heater 2 active", "is_e2_active"),
    ):
        entities.append(
            Wab11BinarySensor(
                main,
                entry,
                runtime_data,
                key=key,
                name=name,
                is_on_fn=lambda data, attribute=attribute: getattr(
                    data.secondary_heat, attribute
                ),
                device_class=BinarySensorDeviceClass.HEAT,
            )
        )

    for key, name, attribute in (
        ("sg_ready_1", "SG-Ready input 1", "sg_ready_1"),
        ("sg_ready_2", "SG-Ready input 2", "sg_ready_2"),
        ("input_h12", "Input H1.2", "input_h12"),
        ("input_h13", "Input H1.3", "input_h13"),
        ("input_h14", "Input H1.4", "input_h14"),
        ("input_h15", "Input H1.5", "input_h15"),
        ("input_de1", "Input DE1", "input_de1"),
        ("input_de2", "Input DE2", "input_de2"),
    ):
        entities.append(
            Wab11BinarySensor(
                main,
                entry,
                runtime_data,
                key=key,
                name=name,
                is_on_fn=lambda data, attribute=attribute: getattr(
                    data.inputs, attribute
                ),
            )
        )

    async_add_entities(entities)
