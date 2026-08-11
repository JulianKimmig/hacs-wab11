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
    async_add_entities(
        [
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
                key="hot_water_charging",
                name="Hot water charging",
                is_on_fn=lambda data: data.hot_water.is_charging,
                device_class=BinarySensorDeviceClass.HEAT,
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
    )
