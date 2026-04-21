"""Constants for the Dira Shabat integration."""
from __future__ import annotations

DOMAIN = "dira_shabat"
MANUFACTURER = "Dira Shabat"
DEVICE_NAME = "Dira Shabat"

# Config keys
CONF_RESET_DELAY = "reset_delay"
CONF_LANGUAGE = "language"
CONF_DIASPORA = "diaspora"
CONF_CANDLE_LIGHTING_OFFSET = "candle_lighting_offset"
CONF_HAVDALAH_OFFSET = "havdalah_offset"

# Defaults
DEFAULT_DIASPORA = True
DEFAULT_RESET_DELAY = 30
DEFAULT_LANGUAGE = "es"
DEFAULT_CANDLE_LIGHTING_OFFSET = 18
DEFAULT_HAVDALAH_OFFSET = 0

# Entity keys (English suffixes used for unique_id and entity_id)
SWITCH_MODO_SHABAT = "shabbat_mode"
SWITCH_FORZAR_MOSTRAR = "force_show"

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

# Migration: rename old Spanish unique_id suffixes to English (v2.2+)
# Key = old suffix, Value = new suffix
UNIQUE_ID_RENAMES = {
    # sensors
    "encendido_velas": "candle_lighting",
    "finaliza": "havdalah",
    "estado": "status",
    "fecha_hebrea": "hebrew_date",
    "iom_tov": "yom_tov",
    "dias_totales": "total_days",
    "dia_actual": "current_day",
    # binary sensors
    "mostrar_horarios": "show_times",
    "cena_hoy": "dinner_today",
    "almuerzo_hoy": "lunch_today",
    "ultimo_dia": "last_day",
    # switches
    "modo_shabat": "shabbat_mode",
    "forzar_mostrar": "force_show",
    "dia_1_cena": "day_1_dinner",
    "dia_1_almuerzo": "day_1_lunch",
    "dia_2_cena": "day_2_dinner",
    "dia_2_almuerzo": "day_2_lunch",
    "dia_3_cena": "day_3_dinner",
    "dia_3_almuerzo": "day_3_lunch",
}

# Internal meal-type → English entity-id suffix
MEAL_SUFFIX = {"cena": "dinner", "almuerzo": "lunch"}

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
