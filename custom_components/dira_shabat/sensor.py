"""Sensor platform for the Dira Shabat integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DEVICE_NAME,
    DOMAIN,
    ICON_CANDLE,
    ICON_MOON,
    ICON_SYNAGOGUE,
    MANUFACTURER,
    TRANSLATIONS,
)
from .coordinator import DiraShabatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dira Shabat sensors from a config entry."""
    coordinator: DiraShabatCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    language = entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    async_add_entities([
        DiraShabatCandleLightingSensor(coordinator, entry, language),
        DiraShabatHavdalahSensor(coordinator, entry, language),
        DiraShabatStatusSensor(coordinator, entry, language),
        DiraShabatHebrewDateSensor(coordinator, entry, language),
        DiraShabatIomTovSensor(coordinator, entry, language),
        DiraShabatHolidayIdSensor(coordinator, entry, language),
        DiraShabatTotalDaysSensor(coordinator, entry, language),
        DiraShabatEndsTodaySensor(coordinator, entry, language),
        DiraShabatCurrentDaySensor(coordinator, entry, language),
    ])


class DiraShabatBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Dira Shabat."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiraShabatCoordinator,
        entry: ConfigEntry,
        language: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._language = language
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )


class DiraShabatCandleLightingSensor(DiraShabatBaseSensor):
    """Sensor for candle lighting time."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_encendido_velas"
        self._attr_name = t["candle_lighting"]
        self._attr_icon = ICON_CANDLE

    @property
    def native_value(self) -> str | None:
        """Return the candle lighting time."""
        if self.coordinator.data:
            return self.coordinator.data.get("candle_lighting_time", "--:--")
        return "--:--"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self.coordinator.data and self.coordinator.data.get("candle_lighting_dt"):
            return {
                "datetime": self.coordinator.data["candle_lighting_dt"].isoformat(),
            }
        return {}


class DiraShabatHavdalahSensor(DiraShabatBaseSensor):
    """Sensor for havdalah time."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_finaliza"
        self._attr_name = t["ends"]
        self._attr_icon = ICON_MOON

    @property
    def native_value(self) -> str | None:
        """Return the havdalah time."""
        if self.coordinator.data:
            return self.coordinator.data.get("havdalah_time", "--:--")
        return "--:--"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self.coordinator.data and self.coordinator.data.get("havdalah_dt"):
            return {
                "datetime": self.coordinator.data["havdalah_dt"].isoformat(),
            }
        return {}


class DiraShabatStatusSensor(DiraShabatBaseSensor):
    """Sensor for current Shabat/Holiday status."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_estado"
        self._attr_name = t["status"]
        self._attr_icon = ICON_SYNAGOGUE

    @property
    def native_value(self) -> str | None:
        """Return the current status."""
        if self.coordinator.data:
            return self.coordinator.data.get("status", "Jol")
        return "Jol"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self.coordinator.data:
            return {
                "holiday_name": self.coordinator.data.get("holiday_name", ""),
                "holiday_type": self.coordinator.data.get("holiday_type", ""),
                "is_yom_tov": self.coordinator.data.get("is_yom_tov", False),
                "issur_melacha": self.coordinator.data.get("issur_melacha", False),
            }
        return {}


class DiraShabatHebrewDateSensor(DiraShabatBaseSensor):
    """Sensor for Hebrew calendar date without year."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_fecha_hebrea"
        self._attr_name = t["hebrew_date"]
        self._attr_icon = "mdi:calendar-star"

    @property
    def native_value(self) -> str | None:
        """Return the Hebrew date."""
        if self.coordinator.data:
            return self.coordinator.data.get("hebrew_date", "")
        return ""


class DiraShabatIomTovSensor(DiraShabatBaseSensor):
    """Sensor indicating if current holiday is Yom Tov."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        self._attr_unique_id = f"{entry.entry_id}_iom_tov"
        self._attr_name = "Iom Tov"
        self._attr_icon = "mdi:star-david"

    @property
    def native_value(self) -> str | None:
        """Return on/off for Yom Tov."""
        if self.coordinator.data:
            return "on" if self.coordinator.data.get("is_yom_tov", False) else "off"
        return "off"


class DiraShabatHolidayIdSensor(DiraShabatBaseSensor):
    """Sensor for the holiday type_id."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        self._attr_unique_id = f"{entry.entry_id}_holiday_id"
        self._attr_name = "Holiday ID"
        self._attr_icon = "mdi:tag"

    @property
    def native_value(self) -> str | None:
        """Return the holiday type_id."""
        if self.coordinator.data:
            return self.coordinator.data.get("holiday_type_id", "")
        return ""


class DiraShabatTotalDaysSensor(DiraShabatBaseSensor):
    """Sensor for total days in the current period."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_dias_totales"
        self._attr_name = t["total_days"]
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int | None:
        """Return total days."""
        if self.coordinator.data:
            return self.coordinator.data.get("total_days", 1)
        return 1

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return period day details."""
        if self.coordinator.data:
            return {
                "period_days": self.coordinator.data.get("period_days", []),
            }
        return {}


class DiraShabatEndsTodaySensor(DiraShabatBaseSensor):
    """Sensor indicating if Shabat/Hag ends today."""

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_ends_today"
        self._attr_name = t["ends_today"]
        self._attr_icon = "mdi:clock-end"

    @property
    def native_value(self) -> str | None:
        """Return on/off."""
        if self.coordinator.data:
            return "on" if self.coordinator.data.get("ends_today", False) else "off"
        return "off"


class DiraShabatCurrentDaySensor(DiraShabatBaseSensor):
    """Sensor for the current day of the Shabat/Hag period.

    Returns 0 if not in issur melacha, 1/2/3 for the current day.
    Attributes include the day name (e.g. "Shabat", "Pesaj I").
    """

    def __init__(self, coordinator, entry, language):
        """Initialize."""
        super().__init__(coordinator, entry, language)
        t = TRANSLATIONS.get(language, TRANSLATIONS["es"])
        self._attr_unique_id = f"{entry.entry_id}_dia_actual"
        self._attr_name = f"{t['day']} actual" if language == "es" else "Current day"
        self._attr_icon = "mdi:calendar-today"

    @property
    def native_value(self) -> int | None:
        """Return current day number (0 = no issur, 1-3 = day of period)."""
        if self.coordinator.data:
            return self.coordinator.data.get("current_day", 0)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return day name and type info."""
        if not self.coordinator.data:
            return {}
        period_days = self.coordinator.data.get("period_days", [])
        current_day = self.coordinator.data.get("current_day", 0)
        attrs = {
            "day_name": self.coordinator.data.get("current_day_name", ""),
            "total_days": self.coordinator.data.get("total_days", 0),
        }
        if 0 < current_day <= len(period_days):
            day_info = period_days[current_day - 1]
            attrs["is_shabbat"] = day_info.get("is_shabbat", False)
            attrs["is_yom_tov"] = day_info.get("is_yom_tov", False)
            attrs["dinner_weekday"] = day_info.get("dinner_weekday", "")
            attrs["lunch_weekday"] = day_info.get("lunch_weekday", "")
        return attrs
