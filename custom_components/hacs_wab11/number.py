"""Number entities for the WAB11 integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import Wab11MainCoordinator, Wab11MainData, Wab11RuntimeData
from .entity import Wab11CoordinatorEntity


class Wab11Number(Wab11CoordinatorEntity[Wab11MainCoordinator], NumberEntity):
    """Generic number entity for WAB11 settings."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: Wab11MainCoordinator,
        entry: ConfigEntry,
        runtime_data: Wab11RuntimeData,
        *,
        key: str,
        name: str,
        value_fn: Callable[[Wab11MainData], float | None],
        set_value_fn: Callable[[float], Awaitable[Wab11MainData]],
        min_value: float,
        max_value: float,
        step: float,
        native_unit: str,
    ) -> None:
        super().__init__(coordinator, entry, runtime_data, key, name)
        self._value_fn = value_fn
        self._set_value_fn = set_value_fn
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = native_unit

    @property
    def native_value(self) -> float | None:
        return self._value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        snapshot = await self._set_value_fn(value)
        self.coordinator.async_set_updated_data(snapshot)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAB11 number entities."""
    runtime_data = entry.runtime_data
    main = runtime_data.main_coordinator
    entities: list[Wab11Number] = []

    for circuit in main.data.heating_circuits:
        if not circuit.is_configured:
            continue
        circuit_id = circuit.circuit_id

        def comfort_value_fn(
            data: Wab11MainData,
            circuit_id: int = circuit_id,
        ) -> float | None:
            return data.heating_circuits[circuit_id - 1].setpoint_comfort.celsius

        async def comfort_set_fn(
            value: float,
            circuit_id: int = circuit_id,
        ) -> Wab11MainData:
            return await runtime_data.runtime.async_set_heating_setpoint(
                circuit_id, "comfort", value
            )

        def normal_value_fn(
            data: Wab11MainData,
            circuit_id: int = circuit_id,
        ) -> float | None:
            return data.heating_circuits[circuit_id - 1].setpoint_normal.celsius

        async def normal_set_fn(
            value: float,
            circuit_id: int = circuit_id,
        ) -> Wab11MainData:
            return await runtime_data.runtime.async_set_heating_setpoint(
                circuit_id, "normal", value
            )

        def setback_value_fn(
            data: Wab11MainData,
            circuit_id: int = circuit_id,
        ) -> float | None:
            return data.heating_circuits[circuit_id - 1].setpoint_setback.celsius

        async def setback_set_fn(
            value: float,
            circuit_id: int = circuit_id,
        ) -> Wab11MainData:
            return await runtime_data.runtime.async_set_heating_setpoint(
                circuit_id, "setback", value
            )

        entities.extend(
            [
                Wab11Number(
                    main,
                    entry,
                    runtime_data,
                    key=f"hk{circuit_id}_comfort_setpoint",
                    name=f"HK{circuit_id} comfort setpoint",
                    value_fn=comfort_value_fn,
                    set_value_fn=comfort_set_fn,
                    min_value=15.0,
                    max_value=30.0,
                    step=0.5,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
                Wab11Number(
                    main,
                    entry,
                    runtime_data,
                    key=f"hk{circuit_id}_normal_setpoint",
                    name=f"HK{circuit_id} normal setpoint",
                    value_fn=normal_value_fn,
                    set_value_fn=normal_set_fn,
                    min_value=15.0,
                    max_value=30.0,
                    step=0.5,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
                Wab11Number(
                    main,
                    entry,
                    runtime_data,
                    key=f"hk{circuit_id}_setback_setpoint",
                    name=f"HK{circuit_id} setback setpoint",
                    value_fn=setback_value_fn,
                    set_value_fn=setback_set_fn,
                    min_value=10.0,
                    max_value=25.0,
                    step=0.5,
                    native_unit=UnitOfTemperature.CELSIUS,
                ),
            ]
        )

    entities.extend(
        [
            Wab11Number(
                main,
                entry,
                runtime_data,
                key="hot_water_normal_setpoint",
                name="Hot water normal setpoint",
                value_fn=lambda data: data.hot_water.setpoint_normal.celsius,
                set_value_fn=lambda value: (
                    runtime_data.runtime.async_set_hot_water_setpoint(
                        "normal",
                        value,
                    )
                ),
                min_value=30.0,
                max_value=65.0,
                step=1.0,
                native_unit=UnitOfTemperature.CELSIUS,
            ),
            Wab11Number(
                main,
                entry,
                runtime_data,
                key="hot_water_setback_setpoint",
                name="Hot water setback setpoint",
                value_fn=lambda data: data.hot_water.setpoint_setback.celsius,
                set_value_fn=lambda value: (
                    runtime_data.runtime.async_set_hot_water_setpoint(
                        "setback",
                        value,
                    )
                ),
                min_value=20.0,
                max_value=60.0,
                step=1.0,
                native_unit=UnitOfTemperature.CELSIUS,
            ),
            Wab11Number(
                main,
                entry,
                runtime_data,
                key="hot_water_push_minutes",
                name="Hot water push minutes",
                value_fn=lambda data: float(data.hot_water.push_minutes),
                set_value_fn=lambda value: (
                    runtime_data.runtime.async_set_hot_water_push_minutes(int(value))
                ),
                min_value=0.0,
                max_value=240.0,
                step=5.0,
                native_unit=UnitOfTime.MINUTES,
            ),
        ]
    )

    async_add_entities(entities)
