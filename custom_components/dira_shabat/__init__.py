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
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_CANDLE_LIGHTING_OFFSET,
    CONF_DIASPORA,
    CONF_HAVDALAH_OFFSET,
    CONF_RESET_DELAY,
    DEFAULT_CANDLE_LIGHTING_OFFSET,
    DEFAULT_DIASPORA,
    DEFAULT_HAVDALAH_OFFSET,
    DEFAULT_RESET_DELAY,
    DOMAIN,
    MAX_PERIOD_DAYS,
    PLATFORMS,
    UNIQUE_ID_RENAMES,
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


@callback
def _migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rename old Spanish unique_id suffixes to the new English ones.

    Updates both unique_id and entity_id so existing automations referring
    to the new entity_id pattern start working. Users with custom entity_ids
    (renamed via UI) keep their custom names but the unique_id still
    migrates.
    """
    registry = er.async_get(hass)
    entry_id = entry.entry_id
    for entity in list(registry.entities.values()):
        if entity.config_entry_id != entry_id:
            continue
        old_uid = entity.unique_id
        prefix = f"{entry_id}_"
        if not old_uid.startswith(prefix):
            continue
        old_suffix = old_uid[len(prefix):]
        new_suffix = UNIQUE_ID_RENAMES.get(old_suffix)
        if not new_suffix or new_suffix == old_suffix:
            continue
        new_uid = f"{entry_id}_{new_suffix}"
        # Build the new default entity_id only if the user hasn't customized it
        platform = entity.entity_id.split(".", 1)[0]
        default_old_entity_id = f"{platform}.{DOMAIN}_{old_suffix}"
        updates = {"new_unique_id": new_uid}
        if entity.entity_id == default_old_entity_id:
            updates["new_entity_id"] = f"{platform}.{DOMAIN}_{new_suffix}"
        _LOGGER.info("Migrating %s: %s → %s", entity.entity_id, old_suffix, new_suffix)
        registry.async_update_entity(entity.entity_id, **updates)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dira Shabat from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _migrate_unique_ids(hass, entry)

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

    # Wait for HA to be fully started before wiring listeners
    def _wire_listeners() -> None:
        _setup_issur_listener(hass, entry, coordinator)
        _setup_vacation_listener(hass, entry)

    if hass.state is CoreState.running:
        _wire_listeners()
    else:
        async def _on_started(event):
            _wire_listeners()

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


def _setup_vacation_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply reset whenever vacation_mode flips (ON → freeze, OFF → normal)."""
    from homeassistant.helpers.event import async_track_state_change_event

    vacation_entity = f"switch.{DOMAIN}_vacation_mode"

    @callback
    def _on_vacation_changed(event):
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        if not old or not new or old.state == new.state:
            return
        _LOGGER.info("Vacation mode %s → %s, applying reset", old.state, new.state)
        hass.async_create_task(_async_apply_reset(hass))

    unsub = async_track_state_change_event(hass, [vacation_entity], _on_vacation_changed)
    hass.data[DOMAIN][entry.entry_id]["unsub_listeners"].append(unsub)


def _entity_on(hass: HomeAssistant, entity_id: str, fallback: bool = False) -> bool:
    """Return whether an entity state is 'on' (fallback if missing)."""
    state = hass.states.get(entity_id)
    return state.state == "on" if state else fallback


async def _async_apply_reset(hass: HomeAssistant) -> None:
    """Apply the current mode (vacation / normal) to Shabat mode + meal switches."""
    if _entity_on(hass, f"switch.{DOMAIN}_vacation_mode"):
        _LOGGER.info("Vacation mode ON — Shabat mode stays OFF")
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": f"switch.{DOMAIN}_shabbat_mode"}
        )
        return

    _LOGGER.info("Resetting Shabat mode ON + meals to Auto-on defaults")
    default_cena = _entity_on(hass, f"switch.{DOMAIN}_auto_on_dinner", fallback=True)
    default_almuerzo = _entity_on(hass, f"switch.{DOMAIN}_auto_on_lunch", fallback=True)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": f"switch.{DOMAIN}_shabbat_mode"}
    )
    for day_num in range(1, MAX_PERIOD_DAYS + 1):
        for meal_en, default in (("dinner", default_cena), ("lunch", default_almuerzo)):
            entity_id = f"switch.{DOMAIN}_day_{day_num}_{meal_en}"
            if hass.states.get(entity_id):
                service = "turn_on" if default else "turn_off"
                await hass.services.async_call(
                    "switch", service, {"entity_id": entity_id}
                )


async def _async_reset_after_delay(
    hass: HomeAssistant, entry: ConfigEntry, delay: int
) -> None:
    """Reset after issur melacha ends (with debounce delay)."""
    await asyncio.sleep(delay)
    coordinator: DiraShabatCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if (coordinator.data or {}).get("issur_melacha"):
        _LOGGER.info("Issur melacha came back on, skipping reset")
        return
    await _async_apply_reset(hass)


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
