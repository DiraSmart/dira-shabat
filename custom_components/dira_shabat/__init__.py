"""The Dira Shabat integration."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DEFAULT_ALMUERZO,
    CONF_DEFAULT_CENA,
    CONF_RESET_DELAY,
    DEFAULT_ALMUERZO,
    DEFAULT_CENA,
    DEFAULT_RESET_DELAY,
    DOMAIN,
    JC_ISSUR_MELACHA,
    MAX_PERIOD_DAYS,
    PLATFORMS,
)
from .coordinator import DiraShabatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dira Shabat from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Register the Lovelace card JS file as a static path
    hass.http.register_static_path(
        f"/{DOMAIN}/dira-shabat-card.js",
        str(Path(__file__).parent / "www" / "dira-shabat-card.js"),
        cache_headers=True,
    )

    coordinator = DiraShabatCoordinator(hass, entry.entry_id)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "unsub_listeners": [],
    }

    # Wait for HA to be fully started before setting up listeners
    if hass.state is CoreState.running:
        await _async_setup_listeners(hass, entry, coordinator)
    else:
        async def _on_started(event):
            await _async_setup_listeners(hass, entry, coordinator)

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)

    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_setup_listeners(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: DiraShabatCoordinator,
) -> None:
    """Set up state change listeners for automation logic."""
    reset_delay = entry.data.get(CONF_RESET_DELAY, DEFAULT_RESET_DELAY)

    @callback
    def _async_issur_melacha_changed(event):
        """Handle issur melacha state changes for auto-reset."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if not new_state or not old_state:
            return

        if old_state.state == "on" and new_state.state == "off":
            # Issur melacha ended - schedule reset after delay
            _LOGGER.info(
                "Issur melacha ended. Scheduling reset in %s seconds", reset_delay
            )
            hass.async_create_task(_async_reset_after_delay(hass, entry, reset_delay))

    unsub = async_track_state_change_event(
        hass, [JC_ISSUR_MELACHA], _async_issur_melacha_changed
    )
    hass.data[DOMAIN][entry.entry_id]["unsub_listeners"].append(unsub)


async def _async_reset_after_delay(
    hass: HomeAssistant, entry: ConfigEntry, delay: int
) -> None:
    """Reset all meal switches to defaults after a delay."""
    await asyncio.sleep(delay)

    # Verify issur melacha is still off (wasn't a transient state)
    issur_state = hass.states.get(JC_ISSUR_MELACHA)
    if issur_state and issur_state.state == "on":
        _LOGGER.info("Issur melacha came back on, skipping reset")
        return

    _LOGGER.info("Resetting meal switches to defaults")

    default_cena = entry.data.get(CONF_DEFAULT_CENA, DEFAULT_CENA)
    default_almuerzo = entry.data.get(CONF_DEFAULT_ALMUERZO, DEFAULT_ALMUERZO)

    # Reset modo shabat to ON
    modo_entity = f"switch.{DOMAIN}_modo_shabat"
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": modo_entity}
    )

    # Reset all meal switches to defaults
    for day_num in range(1, MAX_PERIOD_DAYS + 1):
        cena_entity = f"switch.{DOMAIN}_dia_{day_num}_cena"
        almuerzo_entity = f"switch.{DOMAIN}_dia_{day_num}_almuerzo"

        cena_service = "turn_on" if default_cena else "turn_off"
        almuerzo_service = "turn_on" if default_almuerzo else "turn_off"

        cena_state = hass.states.get(cena_entity)
        if cena_state:
            await hass.services.async_call(
                "switch", cena_service, {"entity_id": cena_entity}
            )

        almuerzo_state = hass.states.get(almuerzo_entity)
        if almuerzo_state:
            await hass.services.async_call(
                "switch", almuerzo_service, {"entity_id": almuerzo_entity}
            )


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Handle config entry updates."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator = data["coordinator"]
        await coordinator.async_shutdown()
        for unsub in data.get("unsub_listeners", []):
            unsub()

    return unload_ok
