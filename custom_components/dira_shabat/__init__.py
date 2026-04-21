"""The Dira Shabat integration."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, callback
from .const import (
    CONF_CANDLE_LIGHTING_OFFSET,
    CONF_DEFAULT_ALMUERZO,
    CONF_DEFAULT_CENA,
    CONF_DIASPORA,
    CONF_HAVDALAH_OFFSET,
    CONF_RESET_DELAY,
    DEFAULT_ALMUERZO,
    DEFAULT_CANDLE_LIGHTING_OFFSET,
    DEFAULT_CENA,
    DEFAULT_DIASPORA,
    DEFAULT_HAVDALAH_OFFSET,
    DEFAULT_RESET_DELAY,
    DOMAIN,
    MAX_PERIOD_DAYS,
    PLATFORMS,
)
from .coordinator import DiraShabatCoordinator

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "dira-shabat-card.js"
CARD_URL_BASE = f"/local/{CARD_FILENAME}"
CARD_URL_FALLBACK = f"/{DOMAIN}_files/{CARD_FILENAME}"


def _get_version() -> str:
    """Read version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        return json.loads(manifest_path.read_text()).get("version", "0")
    except Exception:  # noqa: BLE001
        return "0"


async def _async_install_card(hass: HomeAssistant) -> None:
    """Copy card JS to /config/www/ and register as Lovelace resource (with version cache-busting)."""
    version = _get_version()
    card_url = f"{CARD_URL_BASE}?v={version}"
    src = Path(__file__).parent / "www" / CARD_FILENAME
    dst = Path(hass.config.path("www", CARD_FILENAME))

    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL_FALLBACK, str(src), False)
        ])
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register static path: %s", err)

    def _copy_file() -> str:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Always overwrite - HACS may preserve mtimes, so compare size+content instead
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            return "unchanged"
        shutil.copy2(src, dst)
        return "copied"

    try:
        result = await hass.async_add_executor_job(_copy_file)
        _LOGGER.info("Card %s at %s (v%s)", result, dst, version)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not copy card: %s - using fallback URL", err)
        try:
            from homeassistant.components.frontend import add_extra_js_url
            add_extra_js_url(hass, f"{CARD_URL_FALLBACK}?v={version}")
        except Exception:  # noqa: BLE001
            pass
        return

    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            return
        resources = getattr(lovelace_data, "resources", None)
        if resources is None and isinstance(lovelace_data, dict):
            resources = lovelace_data.get("resources")
        if resources is None:
            return

        if hasattr(resources, "async_load") and not getattr(resources, "loaded", True):
            await resources.async_load()

        items = list(resources.async_items()) if hasattr(resources, "async_items") else []
        existing = next(
            (r for r in items if r.get("url", "").split("?")[0] == CARD_URL_BASE),
            None,
        )

        if existing is None:
            if hasattr(resources, "async_create_item"):
                await resources.async_create_item({"res_type": "module", "url": card_url})
                _LOGGER.info("Registered Lovelace resource %s", card_url)
        elif existing.get("url") != card_url and hasattr(resources, "async_update_item"):
            await resources.async_update_item(
                existing["id"], {"res_type": "module", "url": card_url}
            )
            _LOGGER.info("Updated Lovelace resource URL to %s", card_url)
    except Exception as err:  # noqa: BLE001
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
    candle_offset = entry.data.get(CONF_CANDLE_LIGHTING_OFFSET, DEFAULT_CANDLE_LIGHTING_OFFSET)
    havdalah_offset = entry.data.get(CONF_HAVDALAH_OFFSET, DEFAULT_HAVDALAH_OFFSET)
    coordinator = DiraShabatCoordinator(
        hass,
        entry.entry_id,
        diaspora=diaspora,
        candle_offset=candle_offset,
        havdalah_offset=havdalah_offset,
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "unsub_listeners": [],
        "prev_issur": None,
    }

    # Wait for HA to be fully started before wiring the reset listener
    if hass.state is CoreState.running:
        _setup_issur_listener(hass, entry, coordinator)
    else:
        async def _on_started(event):
            _setup_issur_listener(hass, entry, coordinator)

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)

    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


def _setup_issur_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: DiraShabatCoordinator,
) -> None:
    """Listen to coordinator updates; fire reset when issur flips on→off."""
    reset_delay = entry.data.get(CONF_RESET_DELAY, DEFAULT_RESET_DELAY)

    @callback
    def _on_update():
        data = coordinator.data or {}
        current = bool(data.get("issur_melacha", False))
        entry_data = hass.data[DOMAIN][entry.entry_id]
        prev = entry_data.get("prev_issur")
        entry_data["prev_issur"] = current

        if prev is True and current is False:
            _LOGGER.info(
                "Issur melacha ended. Scheduling reset in %s seconds", reset_delay
            )
            hass.async_create_task(_async_reset_after_delay(hass, entry, reset_delay))

    unsub = coordinator.async_add_listener(_on_update)
    hass.data[DOMAIN][entry.entry_id]["unsub_listeners"].append(unsub)


async def _async_reset_after_delay(
    hass: HomeAssistant, entry: ConfigEntry, delay: int
) -> None:
    """Reset all meal switches to defaults after a delay."""
    await asyncio.sleep(delay)

    # Verify issur melacha is still off (wasn't a transient state)
    coordinator: DiraShabatCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if (coordinator.data or {}).get("issur_melacha"):
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
