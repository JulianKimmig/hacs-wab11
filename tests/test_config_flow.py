"""Behavioral tests for the WAB11 config and options flows."""

from __future__ import annotations

import pytest
import wab11.client as wab11_client_module
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResultType
from wab11.exceptions import ConnectionError, ValidationError, WAB11Error

from custom_components.hacs_wab11.const import (
    CONF_ENABLE_ADVANCED_SENSORS,
    CONF_ENABLE_ENERGY_SENSORS,
    CONF_ENABLE_WRITE_ENTITIES,
    CONF_ENERGY_SCAN_INTERVAL,
    CONF_MAIN_SCAN_INTERVAL,
    DOMAIN,
)


class FailingConnection:
    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def read_input_registers(self, address: int, count: int = 1) -> list[int]:
        raise ConnectionError("cannot reach device")

    async def read_holding_registers(self, address: int, count: int = 1) -> list[int]:
        raise ConnectionError("cannot reach device")

    async def write_register(self, address: int, value: int) -> None:
        raise AssertionError("config flow validation must not write")

    @property
    def is_connected(self) -> bool:
        return True


async def test_successful_config_flow(hass, integration_data):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=integration_data,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == integration_data[CONF_NAME]
    assert result["data"] == integration_data
    assert result["result"].unique_id == "192.0.2.15:502:1"


async def test_config_flow_rejects_duplicate_entry(
    hass, integration_data, make_mock_config_entry
):
    entry = make_mock_config_entry(integration_data)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=integration_data,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_config_flow_reports_connection_errors(
    hass,
    integration_data,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        wab11_client_module,
        "WAB11Connection",
        lambda config: FailingConnection(),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=integration_data,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.parametrize(
    ("error", "error_key"),
    [
        (ValidationError("invalid controller data"), "invalid_config"),
        (WAB11Error("controller rejected request"), "unknown"),
    ],
)
async def test_config_flow_maps_library_errors(
    hass,
    fake_system_connection,
    integration_data,
    error: WAB11Error,
    error_key: str,
) -> None:
    """Map non-connectivity library failures to stable flow errors.

    Args:
        hass: Home Assistant test instance.
        fake_system_connection: External Modbus test double.
        integration_data: Valid baseline config input.
        error: Library error raised by the external connection.
        error_key: Expected translated config-flow error key.

    Returns:
        None.
    """
    fake_system_connection.read_error = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=integration_data,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_key}


async def test_options_flow_updates_runtime_options(
    hass,
    integration_data,
    integration_options,
    make_mock_config_entry,
) -> None:
    entry = make_mock_config_entry(integration_data, options=integration_options)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    updated_options = {
        CONF_MAIN_SCAN_INTERVAL: 25,
        CONF_ENERGY_SCAN_INTERVAL: 900,
        CONF_ENABLE_WRITE_ENTITIES: True,
        CONF_ENABLE_ENERGY_SENSORS: False,
        CONF_ENABLE_ADVANCED_SENSORS: False,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=updated_options,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == updated_options

    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(entry.entry_id)
