"""Config flow for the Dira Shabat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEFAULT_ALMUERZO,
    CONF_DEFAULT_CENA,
    CONF_LANGUAGE,
    CONF_RESET_DELAY,
    DEFAULT_ALMUERZO,
    DEFAULT_CENA,
    DEFAULT_LANGUAGE,
    DEFAULT_RESET_DELAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DiraShabatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dira Shabat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Dira Shabat",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(
                        {"es": "Español", "en": "English"}
                    ),
                    vol.Required(CONF_DEFAULT_CENA, default=DEFAULT_CENA): bool,
                    vol.Required(
                        CONF_DEFAULT_ALMUERZO, default=DEFAULT_ALMUERZO
                    ): bool,
                    vol.Required(
                        CONF_RESET_DELAY, default=DEFAULT_RESET_DELAY
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return DiraShabatOptionsFlow(config_entry)


class DiraShabatOptionsFlow(OptionsFlow):
    """Handle options flow for Dira Shabat."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry data
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data={**self._config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LANGUAGE,
                        default=current.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    ): vol.In({"es": "Español", "en": "English"}),
                    vol.Required(
                        CONF_DEFAULT_CENA,
                        default=current.get(CONF_DEFAULT_CENA, DEFAULT_CENA),
                    ): bool,
                    vol.Required(
                        CONF_DEFAULT_ALMUERZO,
                        default=current.get(CONF_DEFAULT_ALMUERZO, DEFAULT_ALMUERZO),
                    ): bool,
                    vol.Required(
                        CONF_RESET_DELAY,
                        default=current.get(CONF_RESET_DELAY, DEFAULT_RESET_DELAY),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                }
            ),
        )
