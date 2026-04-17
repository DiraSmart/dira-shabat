"""Data coordinator for the Dira Shabat integration."""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Any

from hdate import HDateInfo
from hdate.holidays import HolidayTypes

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


def _next_shabbat_mevarchim(today: date, diaspora: bool) -> dict[str, Any]:
    """Find the next Shabat Mevarchim and whether we're in the week leading to it.

    Shabat Mevarchim is the last Shabat before Rosh Chodesh.
    We consider "the week" as Sunday through Shabat.
    Note: traditionally not said before Tishrei, but we still report it.
    """
    rosh_chodesh_date = None
    rosh_chodesh_month = ""
    is_tishrei = False
    for offset in range(1, 31):
        check = today + timedelta(days=offset)
        info = HDateInfo(check, diaspora)
        for h in info.holidays:
            if h.name == "rosh_chodesh":
                hd = info.hdate
                if hasattr(hd, 'month') and hasattr(hd.month, 'name'):
                    month_name = str(hd.month.name).replace("_", " ").title()
                else:
                    month_name = str(hd)
                is_tishrei = "tishrei" in month_name.lower()
                rosh_chodesh_date = check
                rosh_chodesh_month = month_name
                break
        if rosh_chodesh_date:
            break

    if not rosh_chodesh_date:
        return {"is_mevarchim_week": False, "mevarchim_date": None, "month_name": ""}

    # Find the Shabat before Rosh Chodesh
    shabat_mevarchim = rosh_chodesh_date
    while shabat_mevarchim.weekday() != 5:  # 5 = Saturday
        shabat_mevarchim -= timedelta(days=1)

    # If we already passed this Shabat, it's not relevant
    if shabat_mevarchim < today:
        return {"is_mevarchim_week": False, "mevarchim_date": None, "month_name": ""}

    # "The week" = Sunday before through the Shabat itself
    sunday_of_week = shabat_mevarchim - timedelta(days=6)  # Sunday
    is_mevarchim_week = sunday_of_week <= today <= shabat_mevarchim
    days_until = (shabat_mevarchim - today).days

    return {
        "is_mevarchim_week": is_mevarchim_week,
        "mevarchim_date": shabat_mevarchim.isoformat(),
        "month_name": rosh_chodesh_month,
        "days_until": days_until,
        "is_today": today == shabat_mevarchim,
        "is_tishrei": is_tishrei,
    }


def _has_issur_melacha(check_date: date, diaspora: bool) -> dict[str, Any]:
    """Check if a specific date has issur melacha using hdate.

    Returns a dict with is_shabbat, is_yom_tov, holiday_name, has_issur.
    The date refers to the DAYTIME (morning/afternoon) of that secular date.
    """
    is_shabbat = check_date.weekday() == 5  # Saturday

    info = HDateInfo(check_date, diaspora)

    holidays = info.holidays
    holiday_name = str(holidays[0]) if holidays else ""
    is_yom_tov = any(h.type == HolidayTypes.YOM_TOV for h in holidays)
    has_issur = is_shabbat or is_yom_tov

    return {
        "is_shabbat": is_shabbat,
        "is_yom_tov": is_yom_tov,
        "holiday_name": holiday_name,
        "has_issur": has_issur,
    }


class DiraShabatCoordinator(DataUpdateCoordinator):
    """Coordinator that listens to Jewish Calendar entities and calculates period days."""

    # Hours to force a recalculation (covers day transitions and key moments)
    CHECKPOINT_HOURS = (6, 12, 17)

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
        self._unsub_checkpoints: list = []

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

        # Schedule daily checkpoints at key hours (06:00, 12:00, 17:00)
        # Ensures correct state even if HA restarts or misses an event
        self._schedule_checkpoints()

    def _schedule_checkpoints(self) -> None:
        """Schedule forced recalculations at checkpoint hours."""
        from homeassistant.helpers.event import async_track_time_change

        @callback
        def _checkpoint(now):
            _LOGGER.debug("Checkpoint recalculation at %s", now.strftime("%H:%M"))
            self.async_set_updated_data(self._calculate_data())

        for hour in self.CHECKPOINT_HOURS:
            self._unsub_checkpoints.append(
                async_track_time_change(self.hass, _checkpoint, hour=hour, minute=0, second=0)
            )

    async def async_shutdown(self) -> None:
        """Clean up listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        for unsub in self._unsub_checkpoints:
            unsub()
        self._unsub_checkpoints.clear()
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

        # Calculate period days using hdate
        period_days = self._calculate_period_days(candle_lighting_dt)

        # Calculate current day number
        # Day transitions at 06:00 AM so automations know about "tonight"
        # before sunset. Day 1 starts at candle lighting, day 2+ at 06:00.
        current_day = 0
        current_day_name = ""
        if is_issur and candle_lighting_dt:
            now = dt_util.now()
            if now >= candle_lighting_dt:
                # First morning after candle lighting = day 1's morning
                first_morning_6am = (candle_lighting_dt + timedelta(days=1)).replace(
                    hour=6, minute=0, second=0, microsecond=0
                )
                if now < first_morning_6am:
                    current_day = 1
                else:
                    # Each subsequent day starts at 06:00 AM
                    days_since = (now - first_morning_6am).days + 2
                    current_day = min(days_since, len(period_days))

                if 0 < current_day <= len(period_days):
                    current_day_name = period_days[current_day - 1].get(
                        "day_name", ""
                    )

        # Tomorrow issur melacha - check directly with hdate
        now = dt_util.now()
        tomorrow = (now + timedelta(days=1)).date()
        tomorrow_info = _has_issur_melacha(tomorrow, self.diaspora)
        tomorrow_issur = tomorrow_info["has_issur"]

        # Is this the last day?
        ultimo_dia = is_issur and not tomorrow_info["has_issur"]

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

        # Shabat Mevarchim
        mevarchim = _next_shabbat_mevarchim(now.date(), self.diaspora)

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
            "mevarchim": mevarchim,
        }

    def _calculate_period_days(
        self, candle_dt: datetime | None
    ) -> list[dict[str, Any]]:
        """Calculate days of issur melacha using hdate.

        Checks each consecutive date starting from candle lighting to see
        if it has issur melacha (Shabbat or Yom Tov).

        Each day represents a Jewish day (sunset to sunset):
        - Cena (dinner): the evening meal at the START of the Jewish day
        - Almuerzo (lunch): the midday meal during the Jewish day
        """
        if not candle_dt:
            return self._default_shabbat_day()

        # The first Jewish day starts at candle_dt (sunset on secular date X)
        # The "morning" of that Jewish day is secular date X+1
        first_morning = candle_dt.date() + timedelta(days=1)

        days = []
        for i in range(MAX_PERIOD_DAYS):
            morning_date = first_morning + timedelta(days=i)
            info = _has_issur_melacha(morning_date, self.diaspora)

            if not info["has_issur"]:
                break  # No more consecutive issur melacha days

            # Evening (dinner) is the night before the morning
            evening_date = morning_date - timedelta(days=1)
            dinner_weekday = evening_date.strftime("%A")
            lunch_weekday = morning_date.strftime("%A")

            # Build day name
            is_shabbat = info["is_shabbat"]
            holiday_name = info["holiday_name"]

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
                "is_yom_tov": info["is_yom_tov"],
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
