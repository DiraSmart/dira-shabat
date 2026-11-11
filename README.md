# Dira Shabat

Custom Home Assistant integration for managing Shabbat and Jewish Holiday (Chagim) modes.

Integración personalizada de Home Assistant para gestionar el modo Shabat y festividades judías (Jaguim).

## Features / Funcionalidades

- **Shabbat Mode**: Automatic `issur_melacha` detection computed locally with `hdate` from your Home Assistant location
- **Multi-day support**: Handles 1, 2, or 3-day holiday periods (Yom Tov + Shabbat)
- **Meal toggles**: Independent dinner/lunch toggles per day of the period
- **Auto-reset**: Configurable defaults that reset after each Shabbat/Holiday ends
- **Custom Lovelace Card**: Beautiful card with times display, mode toggle, and meal switches
- **Bilingual**: Full English and Spanish support

## Requirements / Requisitos

- Home Assistant 2024.1.0 or later
- Home Assistant location (latitude, longitude, time zone, elevation) configured. No other integration is required.

## Installation / Instalación

### Marketplace (Home Assistant 2026.11 or later, recommended)

1. Go to **Settings > Marketplace**, open the menu and choose **Add custom repository**
2. Paste `https://github.com/DiraSmart/dira-shabat`, type **Integration**
3. Open "Dira Shabat" and install, then restart Home Assistant
4. Go to **Settings > Devices & services > Add Integration > Dira Shabat**

The Marketplace needs a connected GitHub account on that Home Assistant instance to check custom repositories for updates.

### HACS (Home Assistant before 2026.11)

1. Add this repository as a custom repository in HACS (type: Integration)
2. Search for "Dira Shabat" and install
3. Restart Home Assistant
4. Go to **Settings > Devices & services > Add Integration > Dira Shabat**

### Manual

1. Copy the `custom_components/dira_shabat/` folder to your `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & services > Add Integration > Dira Shabat**

## Lovelace Card Setup

### Resource

The integration serves the card itself and registers it as a dashboard resource automatically
(`/dira_shabat_files/dira-shabat-card.js?v=<version>`). Nothing to copy or add by hand.

If your dashboards are in YAML mode, add the resource manually in `configuration.yaml`:

```yaml
lovelace:
  resources:
    - url: /dira_shabat_files/dira-shabat-card.js
      type: module
```

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

Copyright (C) 2026 DiraSmart

This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version. See [LICENSE](LICENSE) for the full text.

Este programa es software libre bajo la licencia GNU GPL v3. Puedes usarlo, modificarlo y
redistribuirlo, siempre que las versiones modificadas que distribuyas se publiquen bajo la misma licencia.
