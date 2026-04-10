"""Binary sensor platform for the Dira Shabat integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DEVICE_NAME, DOMAIN, MANUFACTURER, TRANSLATIONS
from .coordinator import DiraShabatCoordinator

_LOGGER = logging.getLogger(__name__)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return device info for grouping all entities under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=DEVICE_NAME,
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dira Shabat binary sensors from a config entry."""
    coordinator: DiraShabatCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    language = entry.data.get("language", "es")

    async_add_entities([
        DiraShabatShowTimesSensor(coordinator, entry, language),
        DiraShabatTomorrowIssurSensor(coordinator, entry, language),
        DiraShabatCenaHoySensor(coordinator, entry, language),
        DiraShabatAlmuerzoHoySensor(coordinator, entry, language),
        DiraShabatNocheEntradaSensor(coordinator, entry, language),
        DiraShabatUltimoDiaSensor(coordinator, entry, language),
    ])


class DiraShabatShowTimesSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating whether to show the Shabat card."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_mostrar_horarios"
        self._attr_device_info = _device_info(entry)
        self._attr_name = t["show_times"]
        self._attr_icon = "mdi:eye"

    @property
    def is_on(self) -> bool | None:
        """Return true if the card should be shown."""
        if not self.coordinator.data:
            return False

        show_card = self.coordinator.data.get("show_card", False)

        # Also check force show switch
        force_show_entity = f"switch.{DOMAIN}_forzar_mostrar"
        force_state = self.hass.states.get(force_show_entity)
        force_show = force_state and force_state.state == "on"

        return show_card or force_show


class DiraShabatTomorrowIssurSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating if tomorrow has issur melacha."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_tomorrow_issur"
        self._attr_device_info = _device_info(entry)
        self._attr_name = t["tomorrow_issur"]
        self._attr_icon = "mdi:calendar-arrow-right"

    @property
    def is_on(self) -> bool | None:
        """Return true if tomorrow has issur melacha."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("tomorrow_issur", False)


class DiraShabatMealTodaySensor(CoordinatorEntity, BinarySensorEntity):
    """Base binary sensor that checks the meal switch for the CURRENT day of the period.

    Resolves which day we're in automatically so automations
    only need: is_state('binary_sensor.dira_shabat_cena_hoy', 'on')
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
        meal_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._meal_type = meal_type
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        meal_label = t["dinner"] if meal_type == "cena" else t["lunch"]
        self._attr_unique_id = f"{entry.entry_id}_{meal_type}_hoy"
        self._attr_device_info = _device_info(entry)
        self._attr_name = f"{meal_label} hoy" if language == "es" else f"{meal_label} today"
        self._attr_icon = "mdi:food-turkey" if meal_type == "cena" else "mdi:food-takeout-box"

    @property
    def is_on(self) -> bool | None:
        """Return true if the meal switch for the current day is on."""
        if not self.coordinator.data:
            return False

        current_day = self.coordinator.data.get("current_day", 0)
        if current_day == 0:
            return False

        # Check the switch for the current day
        switch_entity = f"switch.{DOMAIN}_dia_{current_day}_{self._meal_type}"
        state = self.hass.states.get(switch_entity)
        if state is None:
            return False
        return state.state == "on"

    @property
    def extra_state_attributes(self) -> dict:
        """Return which day and name we resolved to."""
        if not self.coordinator.data:
            return {}
        return {
            "current_day": self.coordinator.data.get("current_day", 0),
            "current_day_name": self.coordinator.data.get("current_day_name", ""),
            "issur_melacha": self.coordinator.data.get("issur_melacha", False),
        }


class DiraShabatCenaHoySensor(DiraShabatMealTodaySensor):
    """Binary sensor: is dinner happening at home TODAY?"""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language, "cena")


class DiraShabatAlmuerzoHoySensor(DiraShabatMealTodaySensor):
    """Binary sensor: is lunch happening at home TODAY?"""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language, "almuerzo")


class DiraShabatNocheEntradaSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor: is TONIGHT the start of a new day of issur?

    ON when:
    - erev_shabbat_hag is on (tonight enters the period), OR
    - issur_melacha is on AND we're NOT on the last day
      (tonight enters the next day of the period)

    OFF when:
    - issur_melacha is on AND we're on the last day
      (tonight the period ENDS with havdalah)
    - No issur and no erev

    This makes automations trivial:
      condition: binary_sensor.dira_shabat_noche_entrada = on
      → only runs on nights that START a new day, never on exit night
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_noche_entrada"
        self._attr_device_info = _device_info(entry)
        if language == "es":
            self._attr_name = "Noche de entrada"
        else:
            self._attr_name = "Entry night"
        self._attr_icon = "mdi:weather-sunset-down"

    @property
    def is_on(self) -> bool | None:
        """Return true if tonight starts a new day of issur."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("noche_entrada", False)

    @property
    def extra_state_attributes(self) -> dict:
        """Return context about the current state."""
        if not self.coordinator.data:
            return {}
        current_day = self.coordinator.data.get("current_day", 0)
        total_days = self.coordinator.data.get("total_days", 1)
        return {
            "current_day": current_day,
            "total_days": total_days,
            "is_last_day": current_day == total_days and current_day > 0,
            "current_day_name": self.coordinator.data.get("current_day_name", ""),
        }


class DiraShabatUltimoDiaSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor: are we on the LAST day of the Shabat/Hag period?

    ON = today is the last day, tonight the period ends (havdalah).
    OFF = not the last day, or not in issur at all.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ultimo_dia"
        self._attr_device_info = _device_info(entry)
        if language == "es":
            self._attr_name = "Último día"
        else:
            self._attr_name = "Last day"
        self._attr_icon = "mdi:clock-end"

    @property
    def is_on(self) -> bool | None:
        """Return true if this is the last day of the period."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("ultimo_dia", False)
