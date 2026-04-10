# Dira Shabat

Custom Home Assistant integration for managing Shabbat and Jewish Holiday (Chagim) modes.

Integración personalizada de Home Assistant para gestionar el modo Shabat y festividades judías (Jaguim).

## Features / Funcionalidades

- **Shabbat Mode**: Automatic toggle based on `issur_melacha` from Jewish Calendar
- **Multi-day support**: Handles 1, 2, or 3-day holiday periods (Yom Tov + Shabbat)
- **Meal toggles**: Independent dinner/lunch toggles per day of the period
- **Auto-reset**: Configurable defaults that reset after each Shabbat/Holiday ends
- **Custom Lovelace Card**: Beautiful card with times display, mode toggle, and meal switches
- **Bilingual**: Full English and Spanish support

## Requirements / Requisitos

- Home Assistant 2024.1.0 or later
- [Jewish Calendar](https://www.home-assistant.io/integrations/jewish_calendar/) integration installed and configured

## Installation / Instalación

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Dira Shabat" and install
3. Restart Home Assistant
4. Go to **Settings > Integrations > Add Integration > Dira Shabat**

### Manual

1. Copy the `custom_components/dira_shabat/` folder to your `config/custom_components/` directory
2. Copy `www/dira-shabat-card.js` to your `config/www/` directory
3. Restart Home Assistant
4. Go to **Settings > Integrations > Add Integration > Dira Shabat**

## Lovelace Card Setup

### Add the resource

Go to **Settings > Dashboards > Resources** and add:

- URL: `/local/dira-shabat-card.js`
- Type: JavaScript Module

### Add the card

In your dashboard, add a manual card with this YAML:

```yaml
type: custom:dira-shabat-card
language: es  # or "en"
entity_prefix: dira_shabat
```

### Card Options

| Option | Default | Description |
|--------|---------|-------------|
| `language` | `es` | Language: `es` (Spanish) or `en` (English) |
| `entity_prefix` | `dira_shabat` | Entity prefix for auto-detection |
| `always_show` | `false` | Always show card (ignore visibility sensor) |
| `show_header` | `true` | Show candle lighting / havdalah times header |

## Entities / Entidades

### Switches
| Entity | Description |
|--------|-------------|
| `switch.dira_shabat_modo_shabat` | Main Shabbat/Holiday mode toggle |
| `switch.dira_shabat_forzar_mostrar` | Force show the card |
| `switch.dira_shabat_dia_1_cena` | Day 1 dinner toggle |
| `switch.dira_shabat_dia_1_almuerzo` | Day 1 lunch toggle |
| `switch.dira_shabat_dia_2_cena` | Day 2 dinner toggle (multi-day only) |
| `switch.dira_shabat_dia_2_almuerzo` | Day 2 lunch toggle (multi-day only) |
| `switch.dira_shabat_dia_3_cena` | Day 3 dinner toggle (multi-day only) |
| `switch.dira_shabat_dia_3_almuerzo` | Day 3 lunch toggle (multi-day only) |

### Sensors
| Entity | Description |
|--------|-------------|
| `sensor.dira_shabat_encendido_velas` | Candle lighting time (HH:MM) |
| `sensor.dira_shabat_finaliza` | Havdalah time (HH:MM) |
| `sensor.dira_shabat_estado` | Current status: "Shabat", "Jag - [name]", "Jol" |
| `sensor.dira_shabat_fecha_hebrea` | Hebrew date (without year) |
| `sensor.dira_shabat_iom_tov` | Yom Tov indicator (on/off) |
| `sensor.dira_shabat_holiday_id` | Holiday type ID |
| `sensor.dira_shabat_dias_totales` | Total days in current period |
| `sensor.dira_shabat_ends_today` | Whether Shabat/Hag ends today |

### Binary Sensors
| Entity | Description |
|--------|-------------|
| `binary_sensor.dira_shabat_mostrar_horarios` | Whether to show the card |
| `binary_sensor.dira_shabat_tomorrow_issur` | Whether tomorrow has issur melacha |

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| Language | Spanish | UI language (English/Spanish) |
| Default Dinner | ON | Default state for dinner toggles after reset |
| Default Lunch | ON | Default state for lunch toggles after reset |
| Reset Delay | 30s | Seconds to wait after issur melacha ends before resetting |

## How it Works

1. The integration monitors the Jewish Calendar's `issur_melacha_in_effect` binary sensor
2. It calculates how many consecutive days of issur melacha there are (1-3 days)
3. For each day, it creates dinner and lunch toggles
4. When issur melacha ends, it waits the configured delay and resets all toggles to defaults
5. The Lovelace card shows/hides automatically based on whether it's erev Shabbat/Hag or during issur melacha

## License

MIT
