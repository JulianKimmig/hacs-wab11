"""Shared fixtures for exercising the HACS WAB11 integration."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import wab11.client as wab11_client_module
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry
from wab11.exceptions import WAB11Error

from custom_components.hacs_wab11.const import (
    CONF_ENABLE_ADVANCED_SENSORS,
    CONF_ENABLE_ENERGY_SENSORS,
    CONF_ENABLE_WRITE_ENTITIES,
    CONF_ENERGY_SCAN_INTERVAL,
    CONF_MAIN_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_ENABLE_ADVANCED_SENSORS,
    DEFAULT_ENABLE_ENERGY_SENSORS,
    DEFAULT_ENABLE_WRITE_ENTITIES,
    DEFAULT_ENERGY_SCAN_INTERVAL,
    DEFAULT_MAIN_SCAN_INTERVAL,
    DOMAIN,
)

pytest_plugins = "pytest_homeassistant_custom_component"

FAKE_SYSTEM_CONFIG_PATH = Path(__file__).parent / "fixtures" / "fake_system.json"


@pytest.fixture(autouse=True)
def load_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable Home Assistant's custom-component loader for every test.

    Args:
        enable_custom_integrations: Plugin fixture that enables custom integrations.

    Returns:
        None.
    """


class ConfigBackedFakeConnection:
    """Fake Modbus connection backed by register blocks from a fixture file."""

    def __init__(
        self,
        *,
        input_blocks: dict[int, list[int]],
        holding_blocks: dict[int, list[int]],
    ) -> None:
        self.input_blocks = {
            address: list(values) for address, values in input_blocks.items()
        }
        self.holding_blocks = {
            address: list(values) for address, values in holding_blocks.items()
        }
        self.writes: list[tuple[int, int]] = []
        self.is_connected = True
        self.read_error: WAB11Error | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ConfigBackedFakeConnection:
        register_blocks = config["register_blocks"]
        return cls(
            input_blocks={
                int(address): values
                for address, values in register_blocks["input"].items()
            },
            holding_blocks={
                int(address): values
                for address, values in register_blocks["holding"].items()
            },
        )

    async def connect(self) -> None:
        self.is_connected = True

    async def disconnect(self) -> None:
        self.is_connected = False

    async def read_input_registers(self, address: int, count: int = 1) -> list[int]:
        return self._read_block(
            self.input_blocks, address, count, register_type="input"
        )

    async def read_holding_registers(self, address: int, count: int = 1) -> list[int]:
        return self._read_block(
            self.holding_blocks, address, count, register_type="holding"
        )

    async def write_register(self, address: int, value: int) -> None:
        self.writes.append((address, value))
        self._write_holding_value(address, value)

    def _read_block(
        self,
        block_map: dict[int, list[int]],
        address: int,
        count: int,
        *,
        register_type: str,
    ) -> list[int]:
        if self.read_error is not None:
            raise self.read_error

        for base_address in sorted(block_map):
            values = block_map[base_address]
            offset = address - base_address
            if offset < 0:
                continue
            if offset + count <= len(values):
                return list(values[offset : offset + count])

        raise AssertionError(
            f"Unexpected {register_type} register read: address={address}, count={count}"
        )

    def _write_holding_value(self, address: int, value: int) -> None:
        for base_address in sorted(self.holding_blocks):
            values = self.holding_blocks[base_address]
            offset = address - base_address
            if 0 <= offset < len(values):
                values[offset] = value
                return

        self.holding_blocks[address] = [value]


@pytest.fixture(autouse=True)
def skip_notifications() -> None:
    """Prevent persistent notification side effects in tests."""
    with (
        patch("homeassistant.components.persistent_notification.async_create"),
        patch("homeassistant.components.persistent_notification.async_dismiss"),
    ):
        yield


@pytest.fixture(scope="session")
def fake_system_config() -> dict[str, Any]:
    return json.loads(FAKE_SYSTEM_CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def fake_system_connection(
    fake_system_config: dict[str, Any],
) -> ConfigBackedFakeConnection:
    return ConfigBackedFakeConnection.from_config(deepcopy(fake_system_config))


@pytest.fixture(autouse=True)
def patch_wab11_connection(
    monkeypatch: pytest.MonkeyPatch,
    fake_system_connection: ConfigBackedFakeConnection,
) -> ConfigBackedFakeConnection:
    monkeypatch.setattr(
        wab11_client_module,
        "WAB11Connection",
        lambda config: fake_system_connection,
    )
    return fake_system_connection


@pytest.fixture
def integration_data() -> dict[str, Any]:
    return {
        CONF_NAME: "WAB11 Test",
        CONF_HOST: "192.0.2.15",
        CONF_PORT: 502,
        CONF_UNIT_ID: 1,
    }


@pytest.fixture
def integration_options() -> dict[str, Any]:
    return {
        CONF_MAIN_SCAN_INTERVAL: DEFAULT_MAIN_SCAN_INTERVAL,
        CONF_ENERGY_SCAN_INTERVAL: DEFAULT_ENERGY_SCAN_INTERVAL,
        CONF_ENABLE_WRITE_ENTITIES: DEFAULT_ENABLE_WRITE_ENTITIES,
        CONF_ENABLE_ENERGY_SENSORS: DEFAULT_ENABLE_ENERGY_SENSORS,
        CONF_ENABLE_ADVANCED_SENSORS: DEFAULT_ENABLE_ADVANCED_SENSORS,
    }


@pytest.fixture
def make_mock_config_entry():
    def factory(
        data: dict[str, Any],
        *,
        options: dict[str, Any] | None = None,
        unique_id: str | None = None,
        title: str | None = None,
    ) -> MockConfigEntry:
        host = data[CONF_HOST]
        port = data[CONF_PORT]
        unit_id = data[CONF_UNIT_ID]
        return MockConfigEntry(
            domain=DOMAIN,
            data=data,
            options=options or {},
            title=title or data.get(CONF_NAME) or host,
            unique_id=unique_id or f"{host}:{port}:{unit_id}",
        )

    return factory
