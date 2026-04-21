"""Data coordinator for the Dira Shabat integration."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from hdate import HDateInfo, Location, Zmanim
from hdate.holidays import HolidayTypes

# Religious holiday types to surface (exclude Israeli national/memorial/modern)
FAST_IDS = frozenset({
    "tzom_gedaliah",
    "asara_btevet",
    "taanit_esther",
    "tzom_tammuz",
    "tisha_bav",
    "yom_kippur",
})
MAJOR_FAST_IDS = frozenset({"tisha_bav", "yom_kippur"})

# Approximate minutes after sunset for tzet hakochavim (stars appearing)
TZET_OFFSET_MIN = 20

RELIGIOUS_TYPES = frozenset({
    HolidayTypes.YOM_TOV,
    HolidayTypes.EREV_YOM_TOV,
    HolidayTypes.HOL_HAMOED,
    HolidayTypes.MELACHA_PERMITTED_HOLIDAY,
    HolidayTypes.FAST_DAY,
    HolidayTypes.MINOR_HOLIDAY,
    HolidayTypes.ROSH_CHODESH,
})

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_CANDLE_LIGHTING_OFFSET,
    DEFAULT_HAVDALAH_OFFSET,
    DOMAIN,
    MAX_PERIOD_DAYS,
)

_LOGGER = logging.getLogger(__name__)


# Traditional daily Tehilim division (by Hebrew day of month, 1-30)
TEHILIM_DAILY = {
    1: "1-9", 2: "10-17", 3: "18-22", 4: "23-28", 5: "29-34",
    6: "35-38", 7: "39-43", 8: "44-48", 9: "49-54", 10: "55-59",
    11: "60-65", 12: "66-68", 13: "69-71", 14: "72-76", 15: "77-78",
    16: "79-82", 17: "83-87", 18: "88-89", 19: "90-96", 20: "97-103",
    21: "104-105", 22: "106-107", 23: "108-112", 24: "113-118",
    25: "119:1-96", 26: "119:97-176", 27: "120-134", 28: "135-139",
    29: "140-144", 30: "145-150",
}

# Weekly Tehilim division (by day of week: Mon=0 ... Sun=6 in Python)
TEHILIM_WEEKLY = {
    6: "1-29",    # Sunday
    0: "30-50",   # Monday
    1: "51-72",   # Tuesday
    2: "73-89",   # Wednesday
    3: "90-106",  # Thursday
    4: "107-119", # Friday
    5: "120-150", # Saturday (Shabbat)
}


def _upcoming_fast(
    today: date,
    diaspora: bool,
    zmanim_for: Any,
) -> dict[str, Any] | None:
    """Find the upcoming (or current) fast day within the next year.

    Returns a dict with name, id, is_major, start_dt, end_dt, is_active,
    or None if no fast in the next 365 days.
    """
    for offset in range(0, 365):
        check = today + timedelta(days=offset)
        info = HDateInfo(check, diaspora)
        fast = next((h for h in info.holidays if h.name in FAST_IDS), None)
        if not fast:
            continue

        zmanim_today = zmanim_for(check)
        is_major = fast.name in MAJOR_FAST_IDS
        start_dt = None
        end_dt = None

        if fast.name == "yom_kippur":
            # Start at candle lighting of erev, end at havdalah
            start_dt = zmanim_for(check - timedelta(days=1)).candle_lighting
            end_dt = zmanim_today.havdalah
        elif fast.name == "tisha_bav":
            # Start at shkia of previous day, end at stars (~20 min after shkia)
            start_dt = zmanim_for(check - timedelta(days=1)).shkia
            shkia_today = zmanim_today.shkia
            end_dt = shkia_today + timedelta(minutes=TZET_OFFSET_MIN) if shkia_today else None
        else:
            # Minor fast: alot hashachar → stars
            start_dt = zmanim_today.alot_hashachar
            shkia_today = zmanim_today.shkia
            end_dt = shkia_today + timedelta(minutes=TZET_OFFSET_MIN) if shkia_today else None

        return {
            "name": str(fast),
            "id": fast.name,
            "is_major": is_major,
            "date": check.isoformat(),
            "start_dt": start_dt,
            "end_dt": end_dt,
        }
    return None


def _has_issur_melacha(check_date: date, diaspora: bool) -> dict[str, Any]:
    """Check if a specific date has issur melacha using hdate."""
    is_shabbat = check_date.weekday() == 5  # Saturday
    info = HDateInfo(check_date, diaspora)
    religious = [h for h in info.holidays if h.type in RELIGIOUS_TYPES]
    holiday_name = ", ".join(str(h) for h in religious)
    is_yom_tov = any(h.type == HolidayTypes.YOM_TOV for h in religious)
    has_issur = is_shabbat or is_yom_tov
    return {
        "is_shabbat": is_shabbat,
        "is_yom_tov": is_yom_tov,
        "holiday_name": holiday_name,
        "has_issur": has_issur,
    }


def _next_shabbat_mevarchim(today: date, diaspora: bool) -> dict[str, Any]:
    """Find the next Shabat Mevarchim (last Shabat before Rosh Chodesh)."""
    rosh_chodesh_date = None
    rosh_chodesh_month = ""
    is_tishrei = False
    for offset in range(1, 31):
        check = today + timedelta(days=offset)
        info = HDateInfo(check, diaspora)
        for h in info.holidays:
            if h.name == "rosh_chodesh":
                hd = info.hdate
                if hasattr(hd, "month") and hasattr(hd.month, "name"):
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

    shabat_mevarchim = rosh_chodesh_date
    while shabat_mevarchim.weekday() != 5:
        shabat_mevarchim -= timedelta(days=1)

    if shabat_mevarchim < today:
        return {"is_mevarchim_week": False, "mevarchim_date": None, "month_name": ""}

    sunday_of_week = shabat_mevarchim - timedelta(days=6)
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


def _tehilim_for_today(check_date: date, day_of_month: int) -> dict[str, Any]:
    """Return today's Tehilim psalms (daily and weekly divisions)."""
    weekday = check_date.weekday()
    return {
        "daily": TEHILIM_DAILY.get(day_of_month, ""),
        "weekly": TEHILIM_WEEKLY.get(weekday, ""),
    }


class DiraShabatCoordinator(DataUpdateCoordinator):
    """Coordinator that calculates all Shabbat/holiday data using hdate directly."""

    CHECKPOINT_HOURS = (6, 12, 17)

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        diaspora: bool = True,
        candle_offset: int = DEFAULT_CANDLE_LIGHTING_OFFSET,
        havdalah_offset: int = DEFAULT_HAVDALAH_OFFSET,
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
        self.candle_offset = candle_offset
        self.havdalah_offset = havdalah_offset
        self._unsub_checkpoints: list = []
        self._location = self._build_location(hass)

    def _build_location(self, hass: HomeAssistant) -> Location:
        """Build an hdate Location from HA's configuration."""
        return Location(
            name=hass.config.location_name or "Home",
            diaspora=self.diaspora,
            latitude=hass.config.latitude,
            longitude=hass.config.longitude,
            altitude=hass.config.elevation or 0,
            timezone=str(hass.config.time_zone),
        )

    def _zmanim(self, d: date) -> Zmanim:
        """Return Zmanim object for a given date."""
        return Zmanim(
            date=d,
            location=self._location,
            candle_lighting_offset=self.candle_offset,
            havdalah_offset=self.havdalah_offset,
        )

    async def async_setup(self) -> None:
        """Schedule daily checkpoint recalculations at key hours."""
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
        for unsub in self._unsub_checkpoints:
            unsub()
        self._unsub_checkpoints.clear()

    async def _async_update_data(self) -> dict[str, Any]:
        """Recalculate all data."""
        return self._calculate_data()

    def _calculate_data(self) -> dict[str, Any]:
        """Calculate all Shabbat/holiday data for the current moment."""
        now = dt_util.now()
        today = now.date()
        info = HDateInfo(today, self.diaspora)
        zmanim_today = self._zmanim(today)

        # Find the upcoming Shabbat/Yom Tov period
        upcoming = info.upcoming_shabbat_or_yom_tov
        period_start = upcoming.first_day.gdate  # First day of the period
        period_end = upcoming.last_day.gdate  # Last day of the period

        # Candle lighting = zmanim of the day BEFORE period_start (erev)
        candle_date = period_start - timedelta(days=1)
        candle_lighting_dt = self._zmanim(candle_date).candle_lighting
        havdalah_dt = self._zmanim(period_end).havdalah

        # Shabbat-specific candle lighting & havdalah
        upcoming_shabbat = info.upcoming_shabbat
        shabbat_date = upcoming_shabbat.gdate
        shabbat_candle_dt = self._zmanim(shabbat_date - timedelta(days=1)).candle_lighting
        shabbat_havdalah_dt = self._zmanim(shabbat_date).havdalah

        if candle_lighting_dt:
            candle_lighting_dt = dt_util.as_local(candle_lighting_dt)
        if havdalah_dt:
            havdalah_dt = dt_util.as_local(havdalah_dt)
        if shabbat_candle_dt:
            shabbat_candle_dt = dt_util.as_local(shabbat_candle_dt)
        if shabbat_havdalah_dt:
            shabbat_havdalah_dt = dt_util.as_local(shabbat_havdalah_dt)

        candle_lighting_time = self._format_time(candle_lighting_dt)
        havdalah_time = self._format_time(havdalah_dt)

        # Current state
        is_issur = zmanim_today.issur_melacha_in_effect(now)
        is_erev = zmanim_today.erev_shabbat_chag(now)
        is_motzei = self._is_motzei(now, havdalah_dt, is_issur, is_erev)

        # Holiday info — filter to religious types and combine if multiple
        religious = [h for h in info.holidays if h.type in RELIGIOUS_TYPES]
        holiday_name = ", ".join(str(h) for h in religious)
        holiday_id = ", ".join(h.name for h in religious)
        is_yom_tov = any(h.type == HolidayTypes.YOM_TOV for h in religious)

        # Status
        if is_issur and is_yom_tov:
            status = f"Jag - {holiday_name}" if holiday_name else "Jag"
        elif is_issur:
            status = "Shabat"
        else:
            status = "Jol"

        # Hebrew date
        hdate_obj = info.hdate
        hebrew_date_full = str(hdate_obj)
        hebrew_date_no_year = hebrew_date_full[:-5] if len(hebrew_date_full) > 5 else hebrew_date_full

        # Day of Hebrew month (for Tehilim)
        day_of_month = getattr(hdate_obj, "day", 1) if hasattr(hdate_obj, "day") else 1

        # Period days breakdown
        period_days = self._calculate_period_days(candle_lighting_dt)

        # Current day within the period (cena transitions at 06:00 AM, almuerzo one day behind)
        current_day_cena = 0
        current_day_almuerzo = 0
        current_day_name = ""
        if is_issur and candle_lighting_dt and now >= candle_lighting_dt:
            first_morning_6am = (candle_lighting_dt + timedelta(days=1)).replace(
                hour=6, minute=0, second=0, microsecond=0
            )
            if now < first_morning_6am:
                current_day_cena = 1
            else:
                days_since = (now - first_morning_6am).days + 2
                current_day_cena = min(days_since, len(period_days))
            current_day_almuerzo = max(1, current_day_cena - 1)
            if 0 < current_day_cena <= len(period_days):
                current_day_name = period_days[current_day_cena - 1].get("day_name", "")

        # Tomorrow issur melacha
        tomorrow = today + timedelta(days=1)
        tomorrow_info = _has_issur_melacha(tomorrow, self.diaspora)
        tomorrow_issur = tomorrow_info["has_issur"]
        ultimo_dia = is_issur and not tomorrow_issur

        # Ends today (final havdalah within 6 hours AND in issur)
        ends_today = False
        if havdalah_dt and is_issur:
            time_until = (havdalah_dt - now).total_seconds() / 3600
            if 0 < time_until < 6:
                ends_today = True

        # Omer
        omer_day = 0
        try:
            omer_obj = info.omer
            if omer_obj is not None:
                omer_day = int(getattr(omer_obj, "total_days", 0) or 0)
        except Exception:  # noqa: BLE001
            omer_day = 0

        # Parasha
        parasha = ""
        try:
            parasha = str(info.parasha or "")
        except Exception:  # noqa: BLE001
            parasha = ""

        # Daf Yomi
        daf_yomi = ""
        try:
            daf_yomi = str(info.daf_yomi or "")
        except Exception:  # noqa: BLE001
            daf_yomi = ""

        # Tehilim
        tehilim = _tehilim_for_today(today, day_of_month)

        # Shabat Mevarchim
        mevarchim = _next_shabbat_mevarchim(today, self.diaspora)

        # Upcoming / current fast
        fast = _upcoming_fast(today, self.diaspora, self._zmanim)
        if fast:
            if fast["start_dt"]:
                fast["start_dt"] = dt_util.as_local(fast["start_dt"])
            if fast["end_dt"]:
                fast["end_dt"] = dt_util.as_local(fast["end_dt"])
            fast["is_active"] = bool(
                fast["start_dt"]
                and fast["end_dt"]
                and fast["start_dt"] <= now <= fast["end_dt"]
            )

        # Card visibility
        show_card = is_erev or is_issur

        return {
            "issur_melacha": is_issur,
            "erev_shabbat_hag": is_erev,
            "motzei_shabbat_hag": is_motzei,
            "candle_lighting_time": candle_lighting_time,
            "havdalah_time": havdalah_time,
            "candle_lighting_dt": candle_lighting_dt,
            "havdalah_dt": havdalah_dt,
            "shabbat_candle_dt": shabbat_candle_dt,
            "shabbat_havdalah_dt": shabbat_havdalah_dt,
            "status": status,
            "holiday_name": holiday_name,
            "holiday_id": holiday_id,
            "is_yom_tov": is_yom_tov,
            "hebrew_date": hebrew_date_no_year,
            "hebrew_date_full": hebrew_date_full,
            "period_days": period_days,
            "total_days": len(period_days),
            "ends_today": ends_today,
            "tomorrow_issur": tomorrow_issur,
            "ultimo_dia": ultimo_dia,
            "show_card": show_card,
            "current_day": current_day_cena,
            "current_day_cena": current_day_cena,
            "current_day_almuerzo": current_day_almuerzo,
            "current_day_name": current_day_name,
            "mevarchim": mevarchim,
            "omer": omer_day,
            "parasha": parasha,
            "daf_yomi": daf_yomi,
            "tehilim_daily": tehilim["daily"],
            "tehilim_weekly": tehilim["weekly"],
            "fast": fast,
        }

    def _is_motzei(
        self,
        now: datetime,
        havdalah_dt: datetime | None,
        is_issur: bool,
        is_erev: bool,
    ) -> bool:
        """Return True if we're in the 'motzei' window (just after havdalah, ~45 min)."""
        if is_issur or is_erev or not havdalah_dt:
            return False
        minutes_since = (now - havdalah_dt).total_seconds() / 60
        return 0 < minutes_since < 45

    def _calculate_period_days(
        self, candle_dt: datetime | None
    ) -> list[dict[str, Any]]:
        """Compute the list of consecutive issur melacha days starting from candle lighting."""
        if not candle_dt:
            return self._default_shabbat_day()

        first_morning = candle_dt.date() + timedelta(days=1)
        days = []
        for i in range(MAX_PERIOD_DAYS):
            morning_date = first_morning + timedelta(days=i)
            info = _has_issur_melacha(morning_date, self.diaspora)
            if not info["has_issur"]:
                break

            evening_date = morning_date - timedelta(days=1)
            dinner_weekday = evening_date.strftime("%A")
            lunch_weekday = morning_date.strftime("%A")
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
        """Fallback: a single-day Shabbat."""
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

    def _format_time(self, dt_obj: datetime | None) -> str:
        """Format a datetime as HH:MM (or '--:--' if missing)."""
        if not dt_obj:
            return "--:--"
        return dt_obj.strftime("%H:%M")
