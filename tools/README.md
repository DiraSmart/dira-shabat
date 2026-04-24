# Dira Shabat Scheduler — Tools

Generate Home Assistant automations from a per-client Excel schedule.

## Install

```bash
pip install -r tools/requirements.txt
```

Requirements: Python 3.11 or newer.

## Usage

### 1. Get a `Dispositivos` template

> **Phase 2** will add an HA service that auto-generates the Excel with each client's entities. For Phase 1, fill the template by hand using the structure described below.

### 2. Fill in the schedule

The Excel must have these sheets:

- **`Dispositivos`** — one row per device. Columns: `Area`, `Nombre`, `Tipo`, `entity_id`, `Acepta número`.
- **`En Casa`** — schedule for Shabat/Jag when at least one meal is at home.
- **`Fuera`** — schedule for Shabat/Jag when neither meal is at home.
- **`Diario Lun-Vier`** — weekday schedule (Mon–Fri, not in issur, not erev).

Each schedule sheet has:
- Row 1: area headers (column A blank).
- Row 2: device names (must match `Nombre` from `Dispositivos`).
- Column A: time slots (`HH:MM` or Excel time cells).
- Optional sentinel row `Erev Shabat` in column A — rows below it (until the next blank/non-time row) are treated as before-candle-lighting.
- Cells: `ON`, `OFF`, or a number (depends on domain — see below). Empty cells and color-only cells are skipped.

| Cell value | light | climate | switch | fan | cover | media_player | input_boolean |
|---|---|---|---|---|---|---|---|
| `ON` | turn on (100%) | turn on | turn on | turn on | open | turn on | turn on |
| `OFF` | turn off | turn off | turn off | turn off | close | turn off | turn off |
| Number | brightness % | temperature | (warning) | speed % | position % | volume % | (warning) |

### 3. Generate YAML

```bash
python tools/generate_automations.py path/to/cliente.xlsx --prefix juan --output juan.yaml
```

- `--prefix` is the client identifier; it goes into automation ids and aliases.
- Without `--output`, the YAML is written to stdout.
- A summary (number of automations) goes to stderr.

### 4. Install on the client's HA

Paste the contents of `juan.yaml` into the client's `automations.yaml` (or save as a package file). Reload automations from the UI.

## Conditions used

Generated automations reference these Dira Shabat sensors:

- `binary_sensor.dira_shabat_issur_melacha`
- `binary_sensor.dira_shabat_erev_shabbat_hag`
- `binary_sensor.dira_shabat_dinner_today`
- `binary_sensor.dira_shabat_lunch_today`

Make sure the integration is installed and these sensors exist before importing the YAML.

## Spec

See [`docs/specs/2026-04-23-scheduler-design.md`](../docs/specs/2026-04-23-scheduler-design.md) for the complete design.

## Tests

```bash
pytest
```
