"""Entity helpers for the WAB11 integration."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import Wab11Runtime, Wab11RuntimeData

_CoordinatorT = TypeVar("_CoordinatorT", bound=DataUpdateCoordinator[Any])


class Wab11CoordinatorEntity(CoordinatorEntity[_CoordinatorT], Generic[_CoordinatorT]):
    """Base class for WAB11 coordinator entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        runtime_data: Wab11RuntimeData,
        entity_key: str,
        entity_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._runtime_data = runtime_data
        self._entity_key = entity_key
        self._attr_name = entity_name

    @property
    def runtime(self) -> Wab11Runtime:
        """Return the runtime client wrapper for this entity.

        Returns:
            The config entry's WAB11 runtime wrapper.
        """
        return self._runtime_data.runtime

    @property
    def unique_id(self) -> str:
        entry_id = self._entry.unique_id or self._entry.entry_id
        return f"{entry_id}_{self._entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.runtime.device_identifier)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.runtime.name,
        )
