"""Config flow for the Weishaupt WAB11 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from wab11 import WAB11Client
from wab11.exceptions import ConnectionError, TimeoutError, ValidationError, WAB11Error

from .const import (
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
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MIN_ENERGY_SCAN_INTERVAL,
    MIN_MAIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def _entry_unique_id(data: dict[str, Any]) -> str:
    return f"{data[CONF_HOST]}:{data[CONF_PORT]}:{data[CONF_UNIT_ID]}"


async def async_validate_input(data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input by connecting to the controller."""
    client = WAB11Client(
        data[CONF_HOST],
        port=data[CONF_PORT],
        unit_id=data[CONF_UNIT_ID],
        n_heating_circuits=5,
    )
    try:
        await client.sync()
    finally:
        await client.disconnect()

    return {"title": data.get(CONF_NAME) or data[CONF_HOST]}


class Wab11ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for WAB11."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = _entry_unique_id(user_input)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                info = await async_validate_input(user_input)
            except (ConnectionError, TimeoutError):
                errors["base"] = "cannot_connect"
            except ValidationError:
                errors["base"] = "invalid_config"
            except WAB11Error:
                errors["base"] = "unknown"
            except Exception:  # pragma: no cover - defensive HA flow handling
                _LOGGER.exception("Unexpected exception while validating WAB11 config")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=65535),
                ),
                vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=255),
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "Wab11OptionsFlow":
        """Create the options flow for a config entry.

        Args:
            config_entry: Config entry whose options will be edited.

        Returns:
            A new options flow instance. Home Assistant supplies its config entry.
        """
        return Wab11OptionsFlow()


class Wab11OptionsFlow(config_entries.OptionsFlow):
    """Handle WAB11 options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAIN_SCAN_INTERVAL,
                    default=options.get(
                        CONF_MAIN_SCAN_INTERVAL, DEFAULT_MAIN_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_MAIN_SCAN_INTERVAL)),
                vol.Required(
                    CONF_ENERGY_SCAN_INTERVAL,
                    default=options.get(
                        CONF_ENERGY_SCAN_INTERVAL,
                        DEFAULT_ENERGY_SCAN_INTERVAL,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_ENERGY_SCAN_INTERVAL)),
                vol.Required(
                    CONF_ENABLE_WRITE_ENTITIES,
                    default=options.get(
                        CONF_ENABLE_WRITE_ENTITIES,
                        DEFAULT_ENABLE_WRITE_ENTITIES,
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_ENABLE_ENERGY_SENSORS,
                    default=options.get(
                        CONF_ENABLE_ENERGY_SENSORS,
                        DEFAULT_ENABLE_ENERGY_SENSORS,
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_ENABLE_ADVANCED_SENSORS,
                    default=options.get(
                        CONF_ENABLE_ADVANCED_SENSORS,
                        DEFAULT_ENABLE_ADVANCED_SENSORS,
                    ),
                ): cv.boolean,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
