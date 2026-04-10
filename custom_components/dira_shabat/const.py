"""Constants for the Dira Shabat integration."""
from __future__ import annotations

DOMAIN = "dira_shabat"
MANUFACTURER = "Dira Shabat"
DEVICE_NAME = "Dira Shabat"

# Config keys
CONF_DEFAULT_CENA = "default_cena"
CONF_DEFAULT_ALMUERZO = "default_almuerzo"
CONF_RESET_DELAY = "reset_delay"
CONF_LANGUAGE = "language"

# Defaults
DEFAULT_CENA = True
DEFAULT_ALMUERZO = True
DEFAULT_RESET_DELAY = 30
DEFAULT_LANGUAGE = "es"

# Jewish Calendar entity IDs
JC_ISSUR_MELACHA = "binary_sensor.jewish_calendar_issur_melacha_in_effect"
JC_EREV_SHABBAT_HAG = "binary_sensor.jewish_calendar_erev_shabbat_hag"
JC_CANDLE_LIGHTING = "sensor.jewish_calendar_upcoming_candle_lighting"
JC_HAVDALAH = "sensor.jewish_calendar_upcoming_havdalah"
JC_SHABBAT_CANDLE_LIGHTING = "sensor.jewish_calendar_upcoming_shabbat_candle_lighting"
JC_SHABBAT_HAVDALAH = "sensor.jewish_calendar_upcoming_shabbat_havdalah"
JC_HOLIDAY = "sensor.jewish_calendar_holiday"
JC_DATE = "sensor.jewish_calendar_date"

# Entity keys
SWITCH_MODO_SHABAT = "modo_shabat"
SWITCH_FORZAR_MOSTRAR = "forzar_mostrar"

# Max days in a period (e.g., 3-day Yom Tov + Shabbat)
MAX_PERIOD_DAYS = 3

# Icons
ICON_SYNAGOGUE = "mdi:synagogue"
ICON_CANDLE = "mdi:candle"
ICON_MOON = "mdi:moon-waning-crescent"
ICON_FOOD_DINNER = "mdi:food-turkey"
ICON_FOOD_LUNCH = "mdi:food-takeout-box"
ICON_FORCE_SHOW = "mdi:eye"
ICON_SHABBAT_MODE = "mdi:synagogue"

# Platforms
PLATFORMS = ["switch", "sensor", "binary_sensor"]

# Storage key for persisting switch states
STORAGE_KEY = f"{DOMAIN}_data"
STORAGE_VERSION = 1

# i18n
TRANSLATIONS = {
    "es": {
        "candle_lighting": "Encendido velas",
        "ends": "Finaliza",
        "shabbat_mode": "Modo Shabat",
        "dinner": "Cena",
        "lunch": "Almuerzo",
        "shabbat": "Shabat",
        "chol": "Jol",
        "holiday": "Jag",
        "hebrew_date": "Fecha hebrea",
        "total_days": "Días totales",
        "status": "Estado",
        "show_times": "Mostrar horarios",
        "force_show": "Forzar mostrar",
        "tomorrow_issur": "Mañana issur melacha",
        "ends_today": "Termina hoy",
        "day": "Día",
        "days_of_week": {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        },
    },
    "en": {
        "candle_lighting": "Candle Lighting",
        "ends": "Ends",
        "shabbat_mode": "Shabbat Mode",
        "dinner": "Dinner",
        "lunch": "Lunch",
        "shabbat": "Shabbat",
        "chol": "Weekday",
        "holiday": "Holiday",
        "hebrew_date": "Hebrew Date",
        "total_days": "Total Days",
        "status": "Status",
        "show_times": "Show Times",
        "force_show": "Force Show",
        "tomorrow_issur": "Tomorrow Issur Melacha",
        "ends_today": "Ends Today",
        "day": "Day",
        "days_of_week": {
            "Monday": "Monday",
            "Tuesday": "Tuesday",
            "Wednesday": "Wednesday",
            "Thursday": "Thursday",
            "Friday": "Friday",
            "Saturday": "Saturday",
            "Sunday": "Sunday",
        },
    },
}
