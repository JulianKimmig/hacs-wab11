"""Select entities for the WAB11 integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import HEATING_MODE_OPTIONS, SYSTEM_MODE_OPTIONS
from .coordinator import Wab11MainCoordinator, Wab11MainData, Wab11RuntimeData
from .entity import Wab11CoordinatorEntity


class Wab11Select(Wab11CoordinatorEntity[Wab11MainCoordinator], SelectEntity):
    """Generic WAB11 select entity."""

    def __init__(
        self,
        coordinator: Wab11MainCoordinator,
        entry: ConfigEntry,
        runtime_data: Wab11RuntimeData,
        *,
        key: str,
        name: str,
        options: list[str],
        current_option_fn: Callable[[Wab11MainData], str | None],
        select_fn: Callable[[str], Awaitable[Wab11MainData]],
    ) -> None:
        super().__init__(coordinator, entry, runtime_data, key, name)
        self._attr_options = options
        self._current_option_fn = current_option_fn
        self._select_fn = select_fn

    @property
    def current_option(self) -> str | None:
        return self._current_option_fn(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        snapshot = await self._select_fn(option)
        self.coordinator.async_set_updated_data(snapshot)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAB11 select entities."""
    runtime_data = entry.runtime_data
    main = runtime_data.main_coordinator

    def system_mode_getter(data: Wab11MainData) -> str | None:
        return data.system.system_mode.name.lower()

    entities: list[Wab11Select] = [
        Wab11Select(
            main,
            entry,
            runtime_data,
            key="system_mode",
            name="System mode",
            options=list(SYSTEM_MODE_OPTIONS),
            current_option_fn=system_mode_getter,
            select_fn=runtime_data.runtime.async_set_system_mode,
        )
    ]

    for circuit in main.data.heating_circuits:
        if not circuit.is_configured:
            continue
        circuit_id = circuit.circuit_id

        def current_option_fn(
            data: Wab11MainData, circuit_id: int = circuit_id
        ) -> str | None:
            return data.heating_circuits[circuit_id - 1].mode.name.lower()

        async def select_fn(
            option: str,
            circuit_id: int = circuit_id,
        ) -> Wab11MainData:
            return await runtime_data.runtime.async_set_heating_mode(circuit_id, option)

        entities.append(
            Wab11Select(
                main,
                entry,
                runtime_data,
                key=f"hk{circuit_id}_mode",
                name=f"HK{circuit_id} mode",
                options=list(HEATING_MODE_OPTIONS),
                current_option_fn=current_option_fn,
                select_fn=select_fn,
            )
        )

    async_add_entities(entities)
