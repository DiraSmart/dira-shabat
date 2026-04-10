"""Data coordinator for the Dira Shabat integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from math import ceil
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    JC_CANDLE_LIGHTING,
    JC_EREV_SHABBAT_HAG,
    JC_HAVDALAH,
    JC_HOLIDAY,
    JC_ISSUR_MELACHA,
    JC_SHABBAT_CANDLE_LIGHTING,
    JC_SHABBAT_HAVDALAH,
    JC_DATE,
    MAX_PERIOD_DAYS,
)

_LOGGER = logging.getLogger(__name__)


class DiraShabatCoordinator(DataUpdateCoordinator):
    """Coordinator that listens to Jewish Calendar entities and calculates period days."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, diaspora: bool = True
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.entry_id = entry_id
        self.diaspora = diaspora
        self._unsub_listeners: list = []

    async def async_setup(self) -> None:
        """Set up state change listeners for Jewish Calendar entities."""
        entities_to_track = [
            JC_ISSUR_MELACHA,
            JC_EREV_SHABBAT_HAG,
            JC_CANDLE_LIGHTING,
            JC_HAVDALAH,
            JC_SHABBAT_CANDLE_LIGHTING,
            JC_SHABBAT_HAVDALAH,
            JC_HOLIDAY,
        ]

        @callback
        def _async_state_changed(event):
            """Handle state changes from Jewish Calendar."""
            self.async_set_updated_data(self._calculate_data())

        for entity_id in entities_to_track:
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, [entity_id], _async_state_changed
                )
            )

    async def async_shutdown(self) -> None:
        """Clean up listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Jewish Calendar sensors."""
        return self._calculate_data()

    def _calculate_data(self) -> dict[str, Any]:
        """Calculate all data from Jewish Calendar state."""
        hass = self.hass

        # Get raw states from Jewish Calendar
        issur_melacha = self._get_state(JC_ISSUR_MELACHA)
        erev_shabbat_hag = self._get_state(JC_EREV_SHABBAT_HAG)
        candle_lighting_str = self._get_state(JC_CANDLE_LIGHTING)
        havdalah_str = self._get_state(JC_HAVDALAH)
        shabbat_havdalah_str = self._get_state(JC_SHABBAT_HAVDALAH)
        holiday_name = self._get_state(JC_HOLIDAY)
        hebrew_date = self._get_state(JC_DATE)

        # Holiday attributes
        holiday_state = hass.states.get(JC_HOLIDAY)
        holiday_type = ""
        holiday_type_id = ""
        if holiday_state and holiday_state.attributes:
            holiday_type = holiday_state.attributes.get("type", "")
            holiday_type_id = holiday_state.attributes.get("type_id", "")

        # Parse times
        candle_lighting_dt = self._parse_datetime(candle_lighting_str)
        havdalah_dt = self._parse_datetime(havdalah_str)

        # Format times for display (HH:MM)
        candle_lighting_time = self._format_time(candle_lighting_dt)
        havdalah_time = self._format_time(havdalah_dt)

        # Determine current status
        is_issur = issur_melacha == "on"
        is_erev = erev_shabbat_hag == "on"
        is_yom_tov = self._is_yom_tov(holiday_type)

        if is_issur and is_yom_tov:
            status = f"Jag - {holiday_name}" if holiday_name else "Jag"
        elif is_issur:
            status = "Shabat"
        else:
            status = "Jol"

        # Calculate period days from candle lighting and havdalah times
        period_days = self._calculate_period_days(
            candle_lighting_dt, havdalah_dt, holiday_name
        )

        # Calculate current day number
        current_day = 0
        current_day_name = ""
        if is_issur and candle_lighting_dt:
            now = dt_util.now()
            hours_since = (now - candle_lighting_dt).total_seconds() / 3600
            if hours_since >= 0:
                current_day = min(int(hours_since // 24) + 1, len(period_days))
                if 0 < current_day <= len(period_days):
                    current_day_name = period_days[current_day - 1].get(
                        "day_name", ""
                    )

        # Tomorrow issur melacha - derive from period span
        now = dt_util.now()
        tomorrow_issur = False
        if is_issur and havdalah_dt:
            # If havdalah is more than ~28 hours away, tomorrow also has issur
            hours_until_havdalah = (havdalah_dt - now).total_seconds() / 3600
            tomorrow_issur = hours_until_havdalah > 28
        elif is_erev:
            # Tomorrow starts with the period that begins tonight
            tomorrow_issur = True

        # Is this the last day?
        ultimo_dia = is_issur and not tomorrow_issur

        # Check if Shabat/Hag ends today
        ends_today = False
        if havdalah_dt:
            time_until = (havdalah_dt - now).total_seconds() / 3600
            if 0 < time_until < 6 and shabbat_havdalah_str == havdalah_str:
                ends_today = True

        # Hebrew date without year
        hebrew_date_no_year = ""
        if hebrew_date and hebrew_date not in ("unknown", "unavailable"):
            hebrew_date_no_year = (
                hebrew_date[:-5] if len(hebrew_date) > 5 else hebrew_date
            )

        # Should show card
        show_card = is_erev or is_issur

        return {
            "issur_melacha": is_issur,
            "erev_shabbat_hag": is_erev,
            "candle_lighting_time": candle_lighting_time,
            "havdalah_time": havdalah_time,
            "candle_lighting_dt": candle_lighting_dt,
            "havdalah_dt": havdalah_dt,
            "status": status,
            "holiday_name": holiday_name or "",
            "holiday_type": holiday_type,
            "holiday_type_id": holiday_type_id,
            "is_yom_tov": is_yom_tov,
            "hebrew_date": hebrew_date_no_year,
            "period_days": period_days,
            "total_days": len(period_days),
            "ends_today": ends_today,
            "tomorrow_issur": tomorrow_issur,
            "ultimo_dia": ultimo_dia,
            "show_card": show_card,
            "current_day": current_day,
            "current_day_name": current_day_name,
        }

    def _calculate_period_days(
        self,
        candle_dt: datetime | None,
        havdalah_dt: datetime | None,
        holiday_name: str,
    ) -> list[dict[str, Any]]:
        """Calculate days of issur melacha from candle lighting to havdalah.

        Uses the time span between candle lighting and havdalah to determine
        how many days the period lasts, and checks each date for Shabbat.
        """
        if not candle_dt or not havdalah_dt:
            return self._default_shabbat_day()

        # Calculate number of days from the time span
        span_hours = (havdalah_dt - candle_dt).total_seconds() / 3600
        num_days = min(max(ceil(span_hours / 24), 1), MAX_PERIOD_DAYS)

        # The first Jewish day starts at candle_dt (sunset on secular date X)
        # The "morning" of that Jewish day is secular date X+1
        first_morning = candle_dt.date() + timedelta(days=1)

        days = []
        for i in range(num_days):
            morning_date = first_morning + timedelta(days=i)
            evening_date = morning_date - timedelta(days=1)

            is_shabbat = morning_date.weekday() == 5  # Saturday
            dinner_weekday = evening_date.strftime("%A")
            lunch_weekday = morning_date.strftime("%A")

            # Build day name
            if is_shabbat and holiday_name:
                day_name = f"{holiday_name} - Shabat"
            elif is_shabbat:
                day_name = "Shabat"
            elif holiday_name:
                day_name = holiday_name
            else:
                day_name = "Shabat"

            days.append({
                "day_number": i + 1,
                "day_name": day_name,
                "dinner_weekday": dinner_weekday,
                "lunch_weekday": lunch_weekday,
                "is_shabbat": is_shabbat,
                "is_yom_tov": bool(holiday_name) and not is_shabbat,
                "day_start": evening_date.isoformat(),
                "day_morning": morning_date.isoformat(),
            })

        return days if days else self._default_shabbat_day()

    def _default_shabbat_day(self) -> list[dict[str, Any]]:
        """Return a default single Shabbat day structure."""
        return [{
            "day_number": 1,
            "day_name": "Shabat",
            "dinner_weekday": "Friday",
            "lunch_weekday": "Saturday",
            "is_shabbat": True,
            "is_yom_tov": False,
            "day_start": "",
            "day_morning": "",
        }]

    def _is_yom_tov(self, holiday_type: str) -> bool:
        """Check if the holiday type represents Yom Tov (issur melacha)."""
        if not holiday_type:
            return False
        return holiday_type not in ("", "MEMORIAL_DAY", "MODERN_HOLIDAY")

    def _get_state(self, entity_id: str) -> str:
        """Get entity state safely."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return ""
        if state.state in ("unknown", "unavailable"):
            return ""
        return state.state

    def _parse_datetime(self, dt_str: str) -> datetime | None:
        """Parse ISO datetime string to datetime object."""
        if not dt_str:
            return None
        try:
            parsed = dt_util.parse_datetime(dt_str)
            if parsed:
                return dt_util.as_local(parsed)
            return None
        except (ValueError, TypeError):
            return None

    def _format_time(self, dt_obj: datetime | None) -> str:
        """Format datetime to HH:MM string."""
        if not dt_obj:
            return "--:--"
        return dt_obj.strftime("%H:%M")
