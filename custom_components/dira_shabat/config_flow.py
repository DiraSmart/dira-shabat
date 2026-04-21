"""Config flow for the Dira Shabat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_CANDLE_LIGHTING_OFFSET,
    CONF_DIASPORA,
    CONF_HAVDALAH_OFFSET,
    CONF_LANGUAGE,
    CONF_RESET_DELAY,
    DEFAULT_CANDLE_LIGHTING_OFFSET,
    DEFAULT_DIASPORA,
    DEFAULT_HAVDALAH_OFFSET,
    DEFAULT_LANGUAGE,
    DEFAULT_RESET_DELAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _schema(current: dict[str, Any] | None = None) -> vol.Schema:
    """Build a shared schema for config and options flows."""
    current = current or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_LANGUAGE,
                default=current.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            ): vol.In({"es": "Español", "en": "English"}),
            vol.Required(
                CONF_DIASPORA,
                default=current.get(CONF_DIASPORA, DEFAULT_DIASPORA),
            ): bool,
            vol.Required(
                CONF_CANDLE_LIGHTING_OFFSET,
                default=current.get(CONF_CANDLE_LIGHTING_OFFSET, DEFAULT_CANDLE_LIGHTING_OFFSET),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
            vol.Required(
                CONF_HAVDALAH_OFFSET,
                default=current.get(CONF_HAVDALAH_OFFSET, DEFAULT_HAVDALAH_OFFSET),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
            vol.Required(
                CONF_RESET_DELAY,
                default=current.get(CONF_RESET_DELAY, DEFAULT_RESET_DELAY),
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
        }
    )


class DiraShabatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dira Shabat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Dira Shabat", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return DiraShabatOptionsFlow()


class DiraShabatOptionsFlow(OptionsFlow):
    """Handle options flow for Dira Shabat."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.config_entry.data),
        )
