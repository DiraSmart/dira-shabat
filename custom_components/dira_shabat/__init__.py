"""The Dira Shabat integration."""
from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DEFAULT_ALMUERZO,
    CONF_DEFAULT_CENA,
    CONF_DIASPORA,
    CONF_RESET_DELAY,
    DEFAULT_ALMUERZO,
    DEFAULT_CENA,
    DEFAULT_DIASPORA,
    DEFAULT_RESET_DELAY,
    DOMAIN,
    JC_ISSUR_MELACHA,
    MAX_PERIOD_DAYS,
    PLATFORMS,
)
from .coordinator import DiraShabatCoordinator

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "dira-shabat-card.js"
CARD_URL = f"/local/{CARD_FILENAME}"
# Fallback URL served directly from the integration folder
CARD_URL_FALLBACK = f"/{DOMAIN}_files/{CARD_FILENAME}"


async def _async_install_card(hass: HomeAssistant) -> None:
    """Copy card JS to /config/www/ and register as Lovelace resource."""
    src = Path(__file__).parent / "www" / CARD_FILENAME
    dst = Path(hass.config.path("www", CARD_FILENAME))

    _LOGGER.info("Card source: %s (exists=%s)", src, src.exists())
    _LOGGER.info("Card destination: %s", dst)

    # Always register a fallback static path serving directly from the integration
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL_FALLBACK, str(src), False)
        ])
        _LOGGER.info("Registered fallback static path at %s", CARD_URL_FALLBACK)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register static path: %s", err)

    def _copy_file() -> bool:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(src, dst)
            return True
        return False

    copied = False
    try:
        copied = await hass.async_add_executor_job(_copy_file)
        _LOGGER.info(
            "Card %s to %s (size=%s)",
            "copied" if copied else "already up-to-date at",
            dst,
            dst.stat().st_size if dst.exists() else "N/A",
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not copy card to /config/www/: %s - using fallback URL", err)
        # Use fallback URL if copy failed
        try:
            from homeassistant.components.frontend import add_extra_js_url
            add_extra_js_url(hass, CARD_URL_FALLBACK)
        except Exception:  # noqa: BLE001
            pass
        return

    # Register as Lovelace resource (storage mode only)
    try:
        from homeassistant.components.lovelace import LovelaceData  # type: ignore
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            return
        resources = getattr(lovelace_data, "resources", None)
        if resources is None:
            # Some HA versions store it as dict
            resources = lovelace_data.get("resources") if isinstance(lovelace_data, dict) else None
        if resources is None:
            return

        if hasattr(resources, "async_load") and not getattr(resources, "loaded", True):
            await resources.async_load()

        items = list(resources.async_items()) if hasattr(resources, "async_items") else []
        if any(r.get("url", "").split("?")[0] == CARD_URL for r in items):
            return  # Already registered

        if hasattr(resources, "async_create_item"):
            await resources.async_create_item(
                {"res_type": "module", "url": CARD_URL}
            )
            _LOGGER.info("Registered Lovelace resource %s", CARD_URL)
    except Exception as err:  # noqa: BLE001
        # Lovelace in YAML mode or API changed - fall back to add_extra_js_url
        _LOGGER.debug("Could not register Lovelace resource: %s", err)

    # Always inject via frontend as a safety net
    try:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Could not add extra JS URL: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dira Shabat from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Install the Lovelace card automatically
    if not hass.data[DOMAIN].get("frontend_registered"):
        await _async_install_card(hass)
        hass.data[DOMAIN]["frontend_registered"] = True

    diaspora = entry.data.get(CONF_DIASPORA, DEFAULT_DIASPORA)
    coordinator = DiraShabatCoordinator(hass, entry.entry_id, diaspora=diaspora)

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
