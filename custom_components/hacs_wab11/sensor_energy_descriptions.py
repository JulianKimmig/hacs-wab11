"""Legacy and optional electrical energy sensor mappings and calendar metadata."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy

from .sensor_description import Wab11SensorDescription

LEGACY_ENERGY_SENSORS = tuple(
    Wab11SensorDescription(
        key=f"{category}_energy_{period}",
        name=f"{category.replace('_', ' ').title()} energy {period}",
        path=f"{category}.{period}",
        source="energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )
    for category in ("total", "heating", "hot_water", "cooling")
    for period in ("today", "yesterday", "month", "year")
)

ELECTRICAL_ENERGY_SENSORS = tuple(
    Wab11SensorDescription(
        key=f"electrical_energy_{period}",
        name=f"Electrical energy {period}",
        path=f"electrical.{period}",
        source="energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
        # Yesterday is a completed-day aggregate, not an accumulating counter.
        state_class=None
        if period == "yesterday"
        else SensorStateClass.TOTAL_INCREASING,
        available=lambda data: data.electrical is not None,
        suggested_display_precision=0,
    )
    for period in ("today", "yesterday", "month", "year")
)

ENERGY_SENSORS = LEGACY_ENERGY_SENSORS + ELECTRICAL_ENERGY_SENSORS
