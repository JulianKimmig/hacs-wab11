"""The Weishaupt WAB11 integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_CIRCUIT,
    ATTR_ENTRY_ID,
    ATTR_HOURS,
    ATTR_MINUTES,
    ATTR_MODE,
    CONF_ENABLE_WRITE_ENTITIES,
    CONF_ENERGY_SCAN_INTERVAL,
    CONF_MAIN_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_HOT_WATER_PUSH_MINUTES,
    DOMAIN,
    PARTY_PAUSE_MODES,
    PLATFORMS,
    SERVICE_CANCEL_HOT_WATER_PUSH,
    SERVICE_CANCEL_PARTY_PAUSE,
    SERVICE_SET_PARTY_PAUSE,
    SERVICE_TRIGGER_HOT_WATER_PUSH,
    WRITE_PLATFORMS,
)
from .coordinator import (
    Wab11EnergyCoordinator,
    Wab11MainCoordinator,
    Wab11Runtime,
    Wab11RuntimeData,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _get_platforms(entry: ConfigEntry) -> list[Platform]:
    """Return the platforms enabled for a config entry.

    Args:
        entry: WAB11 config entry whose options select platforms.

    Returns:
        Platforms that Home Assistant should forward for setup.
    """
    platforms = list(PLATFORMS)
    if entry.options.get(CONF_ENABLE_WRITE_ENTITIES, False):
        platforms.extend(WRITE_PLATFORMS)
    return platforms


def _resolve_runtime_data(
    hass: HomeAssistant, entry_id: str | None
) -> Wab11RuntimeData:
    """Resolve loaded runtime data for a service action.

    Args:
        hass: Active Home Assistant instance.
        entry_id: Optional target config-entry identifier.

    Returns:
        Runtime data belonging to the selected loaded config entry.

    Raises:
        HomeAssistantError: If no unambiguous loaded entry can be selected.
    """
    entries = {
        entry.entry_id: entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    }
    if not entries:
        raise HomeAssistantError("No WAB11 integrations are loaded")

    if entry_id is None:
        if len(entries) == 1:
            return next(iter(entries.values()))
        raise HomeAssistantError(
            "entry_id is required when multiple WAB11 integrations are configured"
        )

    if entry_id not in entries:
        raise HomeAssistantError(f"Unknown WAB11 entry_id: {entry_id}")

    return entries[entry_id]


async def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SET_PARTY_PAUSE):
        return

    async def async_set_party_pause(call: ServiceCall) -> None:
        runtime_data = _resolve_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        snapshot = await runtime_data.runtime.async_set_party_pause(
            circuit=call.data[ATTR_CIRCUIT],
            mode=call.data[ATTR_MODE],
            hours=call.data[ATTR_HOURS],
        )
        runtime_data.main_coordinator.async_set_updated_data(snapshot)

    async def async_cancel_party_pause(call: ServiceCall) -> None:
        runtime_data = _resolve_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        snapshot = await runtime_data.runtime.async_cancel_party_pause(
            circuit=call.data[ATTR_CIRCUIT]
        )
        runtime_data.main_coordinator.async_set_updated_data(snapshot)

    async def async_trigger_hot_water_push(call: ServiceCall) -> None:
        runtime_data = _resolve_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        snapshot = await runtime_data.runtime.async_trigger_hot_water_push(
            minutes=call.data[ATTR_MINUTES]
        )
        runtime_data.main_coordinator.async_set_updated_data(snapshot)

    async def async_cancel_hot_water_push(call: ServiceCall) -> None:
        runtime_data = _resolve_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        snapshot = await runtime_data.runtime.async_cancel_hot_water_push()
        runtime_data.main_coordinator.async_set_updated_data(snapshot)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PARTY_PAUSE,
        async_set_party_pause,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
                vol.Required(ATTR_CIRCUIT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=5)
                ),
                vol.Required(ATTR_MODE): vol.In(PARTY_PAUSE_MODES),
                vol.Optional(ATTR_HOURS, default=2.0): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0.5, max=12.0),
                ),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_PARTY_PAUSE,
        async_cancel_party_pause,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
                vol.Required(ATTR_CIRCUIT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=5)
                ),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TRIGGER_HOT_WATER_PUSH,
        async_trigger_hot_water_push,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
                vol.Optional(
                    ATTR_MINUTES, default=DEFAULT_HOT_WATER_PUSH_MINUTES
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=0, max=240),
                ),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_HOT_WATER_PUSH,
        async_cancel_hot_water_push,
        schema=vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string}),
    )


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the integration."""
    await _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAB11 from a config entry."""
    runtime = Wab11Runtime(
        name=entry.title,
        host=entry.data["host"],
        port=entry.data["port"],
        unit_id=entry.data[CONF_UNIT_ID],
        main_scan_interval=entry.options.get(
            CONF_MAIN_SCAN_INTERVAL,
            15,
        ),
        energy_scan_interval=entry.options.get(
            CONF_ENERGY_SCAN_INTERVAL,
            300,
        ),
        write_entities_enabled=entry.options.get(CONF_ENABLE_WRITE_ENTITIES, False),
    )
    main_coordinator = Wab11MainCoordinator(hass, entry, runtime)
    energy_coordinator = Wab11EnergyCoordinator(hass, entry, runtime)

    try:
        await main_coordinator.async_config_entry_first_refresh()
        await energy_coordinator.async_refresh()
    except Exception as err:
        await runtime.async_disconnect()
        raise ConfigEntryNotReady(str(err)) from err

    runtime_data = Wab11RuntimeData(
        runtime=runtime,
        main_coordinator=main_coordinator,
        energy_coordinator=energy_coordinator,
        platforms=_get_platforms(entry),
    )
    entry.runtime_data = runtime_data

    await _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(
        entry,
        runtime_data.platforms,
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    runtime_data = entry.runtime_data
    unloaded = await hass.config_entries.async_unload_platforms(
        entry,
        runtime_data.platforms,
    )
    if unloaded:
        await runtime_data.runtime.async_disconnect()
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
