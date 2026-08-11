"""Button entities for the WAB11 integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_HOT_WATER_PUSH_MINUTES
from .coordinator import Wab11MainCoordinator, Wab11MainData, Wab11RuntimeData
from .entity import Wab11CoordinatorEntity


class Wab11Button(Wab11CoordinatorEntity[Wab11MainCoordinator], ButtonEntity):
    """Generic button entity for WAB11 actions."""

    def __init__(
        self,
        coordinator: Wab11MainCoordinator,
        entry: ConfigEntry,
        runtime_data: Wab11RuntimeData,
        *,
        key: str,
        name: str,
        press_fn: Callable[[], Awaitable[Wab11MainData]],
    ) -> None:
        super().__init__(coordinator, entry, runtime_data, key, name)
        self._press_fn = press_fn

    async def async_press(self) -> None:
        snapshot = await self._press_fn()
        self.coordinator.async_set_updated_data(snapshot)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAB11 buttons."""
    runtime_data = entry.runtime_data
    main = runtime_data.main_coordinator

    async def trigger_push() -> Wab11MainData:
        return await runtime_data.runtime.async_trigger_hot_water_push(
            DEFAULT_HOT_WATER_PUSH_MINUTES
        )

    async_add_entities(
        [
            Wab11Button(
                main,
                entry,
                runtime_data,
                key="trigger_hot_water_push",
                name="Trigger hot water push",
                press_fn=trigger_push,
            ),
            Wab11Button(
                main,
                entry,
                runtime_data,
                key="cancel_hot_water_push",
                name="Cancel hot water push",
                press_fn=runtime_data.runtime.async_cancel_hot_water_push,
            ),
        ]
    )
