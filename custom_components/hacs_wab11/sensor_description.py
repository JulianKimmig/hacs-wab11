"""Shared sensor description contract for WAB11 coordinator snapshots."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass


@dataclass(frozen=True, kw_only=True)
class Wab11SensorDescription:
    """Describe one value exposed as a Home Assistant sensor.

    Attributes:
        key: Stable suffix used in the entity unique ID.
        name: Human-readable entity name.
        path: Attribute path below coordinator data.
        source: Coordinator source, either ``main`` or ``energy``.
        device_class: Optional Home Assistant sensor device class.
        native_unit: Optional native unit of measurement.
        state_class: Optional long-term-statistics state class.
        enum: Whether the resolved value is represented by an enum name.
        temperature: Whether the resolved value is a library Temperature.
        force_update: Whether unchanged values are written on every coordinator update.
        enabled_default: Whether the entity is enabled by default.
        available: Optional predicate checked before resolving the attribute path.
        suggested_display_precision: Suggested number of displayed decimal places.
    """

    key: str
    name: str
    path: str
    source: str = "main"
    device_class: SensorDeviceClass | None = None
    native_unit: str | None = None
    state_class: SensorStateClass | None = None
    enum: bool = False
    temperature: bool = False
    force_update: bool = False
    enabled_default: bool = True
    available: Callable[[Any], bool] | None = None
    suggested_display_precision: int | None = None

    def value(self, data: Any) -> Any:
        """Resolve and normalize this value from coordinator data.

        Args:
            data: Main or energy coordinator data object.

        Returns:
            A Home Assistant-compatible native state value.
        """
        value = data
        for part in self.path.split("."):
            value = value[int(part)] if part.isdigit() else getattr(value, part)
        if self.temperature:
            return value.celsius
        if self.enum:
            return value.name.lower()
        return value
