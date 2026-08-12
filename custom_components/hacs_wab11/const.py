"""Constants for the Weishaupt WAB11 integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

NAME: Final = "Weishaupt WAB11"
DOMAIN: Final = "hacs_wab11"
MANUFACTURER: Final = "Weishaupt"
MODEL: Final = "WAB11"
VERSION: Final = "0.2.0"

PLATFORMS: tuple[Platform, ...] = (
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
)
WRITE_PLATFORMS: tuple[Platform, ...] = (
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
)

DATA_RUNTIME: Final = "runtime"
DATA_MAIN_COORDINATOR: Final = "main_coordinator"
DATA_ENERGY_COORDINATOR: Final = "energy_coordinator"
DATA_PLATFORMS: Final = "platforms"

CONF_UNIT_ID = "unit_id"
CONF_N_HEATING_CIRCUITS = "n_heating_circuits"
CONF_MAIN_SCAN_INTERVAL = "main_scan_interval"
CONF_ENERGY_SCAN_INTERVAL = "energy_scan_interval"
CONF_ENABLE_WRITE_ENTITIES = "enable_write_entities"
CONF_ENABLE_ENERGY_SENSORS = "enable_energy_sensors"
CONF_ENABLE_ADVANCED_SENSORS = "enable_advanced_sensors"

DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_MAIN_SCAN_INTERVAL = 15
DEFAULT_ENERGY_SCAN_INTERVAL = 300
DEFAULT_ENABLE_WRITE_ENTITIES = False
DEFAULT_ENABLE_ENERGY_SENSORS = True
DEFAULT_ENABLE_ADVANCED_SENSORS = False
DEFAULT_HOT_WATER_PUSH_MINUTES = 30

MIN_MAIN_SCAN_INTERVAL = 5
MIN_ENERGY_SCAN_INTERVAL = 60

SERVICE_SET_PARTY_PAUSE = "set_party_pause"
SERVICE_CANCEL_PARTY_PAUSE = "cancel_party_pause"
SERVICE_TRIGGER_HOT_WATER_PUSH = "trigger_hot_water_push"
SERVICE_CANCEL_HOT_WATER_PUSH = "cancel_hot_water_push"

ATTR_ENTRY_ID = "entry_id"
ATTR_CIRCUIT = "circuit"
ATTR_MODE = "mode"
ATTR_HOURS = "hours"
ATTR_MINUTES = "minutes"

PARTY_PAUSE_MODES: tuple[str, ...] = ("party", "pause")
SYSTEM_MODE_OPTIONS: tuple[str, ...] = (
    "automatic",
    "heating",
    "cooling",
    "summer",
    "standby",
    "second_heat",
)
HEATING_MODE_OPTIONS: tuple[str, ...] = (
    "automatic",
    "comfort",
    "normal",
    "setback",
    "standby",
)
