"""Coordinator and runtime helpers for the WAB11 integration."""

from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from wab11 import HeatingCircuitMode, SystemMode, WAB11Client
from wab11.exceptions import WAB11Error
from wab11.models.energy import EnergyStatistics
from wab11.models.heat_pump import HeatPumpState
from wab11.models.heating import HeatingCircuit
from wab11.models.hot_water import HotWaterState
from wab11.models.inputs import InputsState
from wab11.models.secondary_heat import SecondaryHeatSourceState
from wab11.models.system import SystemState

from .const import DOMAIN
from .power_estimator import EnergyPowerEstimator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Wab11MainData:
    """Immutable snapshot for the main coordinator."""

    system: SystemState
    heating_circuits: tuple[HeatingCircuit, ...]
    hot_water: HotWaterState
    heat_pump: HeatPumpState
    secondary_heat: SecondaryHeatSourceState
    inputs: InputsState


class Wab11Runtime:
    """Runtime wrapper around the library client."""

    def __init__(
        self,
        *,
        name: str,
        host: str,
        port: int,
        unit_id: int,
        n_heating_circuits: int | None,
        main_scan_interval: int,
        energy_scan_interval: int,
        write_entities_enabled: bool,
    ) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.n_heating_circuits = n_heating_circuits
        self.device_identifier = f"{host}:{port}:{unit_id}"
        self.main_scan_interval = main_scan_interval
        self.energy_scan_interval = energy_scan_interval
        self.write_entities_enabled = write_entities_enabled
        self.client = WAB11Client(
            host,
            port=port,
            unit_id=unit_id,
            n_heating_circuits=n_heating_circuits,
        )
        self._lock = asyncio.Lock()

    def _snapshot_main(self) -> Wab11MainData:
        return Wab11MainData(
            system=deepcopy(self.client.system),
            heating_circuits=tuple(deepcopy(self.client.heating_circuits)),
            hot_water=deepcopy(self.client.hot_water),
            heat_pump=deepcopy(self.client.heat_pump),
            secondary_heat=deepcopy(self.client.secondary_heat),
            inputs=deepcopy(self.client.inputs),
        )

    def _snapshot_energy(self) -> EnergyStatistics:
        return deepcopy(self.client.energy)

    async def async_refresh_main(self) -> Wab11MainData:
        async with self._lock:
            await self.client.sync()
            return self._snapshot_main()

    async def async_refresh_energy(self) -> EnergyStatistics:
        async with self._lock:
            await self.client.sync_energy()
            return self._snapshot_energy()

    async def async_disconnect(self) -> None:
        await self.client.disconnect()

    def _ensure_writes_enabled(self) -> None:
        if not self.write_entities_enabled:
            raise HomeAssistantError("Write entities are disabled for this WAB11 entry")

    async def async_set_system_mode(self, option: str) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.set_system_mode(
                SystemMode[option.upper()], confirmed=True
            )
            return self._snapshot_main()

    async def async_set_heating_mode(self, circuit: int, option: str) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.set_heating_circuit_mode(
                circuit,
                HeatingCircuitMode[option.upper()],
            )
            return self._snapshot_main()

    async def async_set_heating_setpoint(
        self,
        circuit: int,
        level: str,
        value: float,
    ) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.set_heating_circuit_setpoint(circuit, level, value)
            return self._snapshot_main()

    async def async_set_hot_water_setpoint(
        self, level: str, value: float
    ) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.set_hot_water_setpoint(level, value)
            return self._snapshot_main()

    async def async_set_hot_water_push_minutes(self, minutes: int) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.trigger_hot_water_push(minutes)
            return self._snapshot_main()

    async def async_trigger_hot_water_push(self, minutes: int) -> Wab11MainData:
        return await self.async_set_hot_water_push_minutes(minutes)

    async def async_cancel_hot_water_push(self) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.cancel_hot_water_push()
            return self._snapshot_main()

    async def async_set_party_pause(
        self,
        *,
        circuit: int,
        mode: str,
        hours: float,
    ) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.set_heating_party_pause(circuit, mode, hours)
            return self._snapshot_main()

    async def async_cancel_party_pause(self, *, circuit: int) -> Wab11MainData:
        async with self._lock:
            self._ensure_writes_enabled()
            await self.client.set_heating_party_pause(circuit, "auto")
            return self._snapshot_main()


class Wab11MainCoordinator(DataUpdateCoordinator[Wab11MainData]):
    """Coordinator for regularly changing WAB11 state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        runtime: Wab11Runtime,
    ) -> None:
        """Initialize the main state coordinator.

        Args:
            hass: Active Home Assistant instance.
            entry: Config entry that owns this coordinator.
            runtime: Runtime client wrapper used for updates.

        Returns:
            None.
        """
        self.runtime = runtime
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{runtime.device_identifier}_main",
            update_interval=timedelta(seconds=runtime.main_scan_interval),
            always_update=False,
        )

    async def _async_update_data(self) -> Wab11MainData:
        try:
            return await self.runtime.async_refresh_main()
        except WAB11Error as err:
            raise UpdateFailed(str(err)) from err


class Wab11EnergyCoordinator(DataUpdateCoordinator[EnergyStatistics]):
    """Coordinator for low-frequency energy statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        runtime: Wab11Runtime,
    ) -> None:
        """Initialize the energy statistics coordinator.

        Args:
            hass: Active Home Assistant instance.
            entry: Config entry that owns this coordinator.
            runtime: Runtime client wrapper used for updates.

        Returns:
            None.
        """
        self.runtime = runtime
        self.power_estimator = EnergyPowerEstimator()
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{runtime.device_identifier}_energy",
            update_interval=timedelta(seconds=runtime.energy_scan_interval),
            always_update=True,
        )

    async def _async_update_data(self) -> EnergyStatistics:
        try:
            statistics = await self.runtime.async_refresh_energy()
            self.power_estimator.update(statistics, dt_util.now())
            return statistics
        except WAB11Error as err:
            raise UpdateFailed(str(err)) from err


@dataclass(frozen=True, slots=True)
class Wab11RuntimeData:
    """Runtime objects owned by one WAB11 config entry."""

    runtime: Wab11Runtime
    main_coordinator: Wab11MainCoordinator
    energy_coordinator: Wab11EnergyCoordinator
    platforms: list[Platform]
