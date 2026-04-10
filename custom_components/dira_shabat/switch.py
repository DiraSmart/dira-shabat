"""Switch platform for the Dira Shabat integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONF_DEFAULT_ALMUERZO,
    CONF_DEFAULT_CENA,
    DEFAULT_ALMUERZO,
    DEFAULT_CENA,
    DEVICE_NAME,
    DOMAIN,
    ICON_FOOD_DINNER,
    ICON_FOOD_LUNCH,
    ICON_FORCE_SHOW,
    ICON_SHABBAT_MODE,
    MANUFACTURER,
    MAX_PERIOD_DAYS,
    SWITCH_FORZAR_MOSTRAR,
    SWITCH_MODO_SHABAT,
    TRANSLATIONS,
)
from .coordinator import DiraShabatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dira Shabat switches from a config entry."""
    coordinator: DiraShabatCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    language = entry.data.get("language", "es")

    entities: list[SwitchEntity] = [
        DiraShabatModeSwitch(coordinator, entry, language),
        DiraShabatForceShowSwitch(coordinator, entry, language),
    ]

    # Create meal switches for each possible day (up to MAX_PERIOD_DAYS)
    for day_num in range(1, MAX_PERIOD_DAYS + 1):
        entities.append(
            DiraShabatMealSwitch(
                coordinator, entry, day_num, "cena", language
            )
        )
        entities.append(
            DiraShabatMealSwitch(
                coordinator, entry, day_num, "almuerzo", language
            )
        )

    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return device info for grouping all entities under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=DEVICE_NAME,
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
    )


class DiraShabatModeSwitch(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """Switch for Shabbat/Holiday mode."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._language = language
        self._attr_unique_id = f"{entry.entry_id}_{SWITCH_MODO_SHABAT}"
        self._attr_device_info = _device_info(entry)
        self._attr_icon = ICON_SHABBAT_MODE
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_name = t["shabbat_mode"]
        self._is_on = True

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()
        # Sync meal switches
        await self._sync_meal_switches(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()
        # Sync meal switches
        await self._sync_meal_switches(False)

    async def _sync_meal_switches(self, state: bool) -> None:
        """Sync all meal switches to match the mode switch."""
        for day_num in range(1, MAX_PERIOD_DAYS + 1):
            for meal in ("cena", "almuerzo"):
                entity_id = f"switch.{DOMAIN}_dia_{day_num}_{meal}"
                entity_state = self.hass.states.get(entity_id)
                if entity_state:
                    service = "turn_on" if state else "turn_off"
                    await self.hass.services.async_call(
                        "switch", service, {"entity_id": entity_id}
                    )

    async def async_added_to_hass(self) -> None:
        """Restore previous state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self._is_on = last_state.state == "on"


class DiraShabatForceShowSwitch(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """Switch to force show the Shabat card."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._language = language
        self._attr_unique_id = f"{entry.entry_id}_{SWITCH_FORZAR_MOSTRAR}"
        self._attr_device_info = _device_info(entry)
        self._attr_icon = ICON_FORCE_SHOW
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_name = t["force_show"]
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore previous state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self._is_on = last_state.state == "on"


class DiraShabatMealSwitch(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """Dynamic switch for a meal on a specific day of the Shabat/Holiday period."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        day_number: int,
        meal_type: str,  # "cena" or "almuerzo"
        language: str,
    ) -> None:
        """Initialize the meal switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._day_number = day_number
        self._meal_type = meal_type
        self._language = language
        self._attr_unique_id = f"{entry.entry_id}_dia_{day_number}_{meal_type}"
        self._attr_device_info = _device_info(entry)
        self._attr_icon = ICON_FOOD_DINNER if meal_type == "cena" else ICON_FOOD_LUNCH

        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        meal_label = t["dinner"] if meal_type == "cena" else t["lunch"]
        self._attr_name = f"{t['day']} {day_number} - {meal_label}"
        self._meal_label = meal_label

        # Default state from config
        if meal_type == "cena":
            self._is_on = entry.data.get(CONF_DEFAULT_CENA, DEFAULT_CENA)
        else:
            self._is_on = entry.data.get(CONF_DEFAULT_ALMUERZO, DEFAULT_ALMUERZO)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return True if the day exists in the current period."""
        if not self.coordinator.data:
            return self._day_number == 1
        total_days = self.coordinator.data.get("total_days", 1)
        return self._day_number <= total_days

    @property
    def entity_registry_visible_default(self) -> bool:
        """Return True for day 1, False for others (hidden by default)."""
        return self._day_number == 1

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the meal switch."""
        if not self.coordinator.data:
            return {}

        period_days = self.coordinator.data.get("period_days", [])
        if self._day_number <= len(period_days):
            day_info = period_days[self._day_number - 1]
            t = TRANSLATIONS.get(self._language, TRANSLATIONS["es"])
            days_of_week = t["days_of_week"]

            dinner_weekday = days_of_week.get(
                day_info.get("dinner_weekday", ""), day_info.get("dinner_weekday", "")
            )
            lunch_weekday = days_of_week.get(
                day_info.get("lunch_weekday", ""), day_info.get("lunch_weekday", "")
            )

            return {
                "day_name": day_info.get("day_name", ""),
                "day_number": day_info.get("day_number", self._day_number),
                "dinner_weekday": dinner_weekday,
                "lunch_weekday": lunch_weekday,
                "is_shabbat": day_info.get("is_shabbat", False),
                "is_yom_tov": day_info.get("is_yom_tov", False),
                "meal_type": self._meal_type,
            }
        return {}

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()

    def reset_to_default(self) -> None:
        """Reset this switch to the configured default value."""
        if self._meal_type == "cena":
            self._is_on = self._entry.data.get(CONF_DEFAULT_CENA, DEFAULT_CENA)
        else:
            self._is_on = self._entry.data.get(CONF_DEFAULT_ALMUERZO, DEFAULT_ALMUERZO)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore previous state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self._is_on = last_state.state == "on"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update name with day info if available
        if self.coordinator.data:
            period_days = self.coordinator.data.get("period_days", [])
            if self._day_number <= len(period_days):
                day_info = period_days[self._day_number - 1]
                day_name = day_info.get("day_name", f"Día {self._day_number}")
                self._attr_name = f"{day_name} - {self._meal_label}"
        super()._handle_coordinator_update()
