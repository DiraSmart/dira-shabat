# Dira Shabat Scheduler — Design

**Date**: 2026-04-23
**Status**: Approved, ready for implementation plan
**Goal**: Let an integrator generate per-client Home Assistant automations from an Excel schedule, leveraging Dira Shabat sensors as conditions.

---

## Context & flow

Each client has their own Home Assistant instance with the Dira Shabat integration installed. Schedules vary substantially per client (lights, A/Cs, fans, covers, etc. on/off at specific times during Shabbat, holidays and weekdays). The current flow is:

1. **Client → integrator**: client requests a schedule update.
2. **Integrator generates YAML** offline.
3. **Integrator delivers YAML** to client; client pastes it into `automations.yaml` (or as a package file).

The design covers two pieces:

- **An HA service** in the Dira Shabat integration (`dira_shabat.export_devices`) that produces a starting Excel template with the client's actual entities pre-filled.
- **A standalone Python script** (`tools/generate_automations.py`) the integrator runs locally to convert the filled Excel into a YAML automations file.

These two pieces are intentionally decoupled: the integration handles the per-client device snapshot; the integrator handles schedule editing and YAML generation. The client never runs the generator.

---

## Component 1: `dira_shabat.export_devices` service

### Trigger
Called from HA Developer Tools → Services, or from an automation. No parameters required.

### Behaviour
- Iterates the area registry.
- For each area, collects entities from controllable domains assigned to that area.
- Writes an `.xlsx` file to `/config/dira_shabat_devices.xlsx` (overwrites if exists).

### Controllable domains included
| Domain | Numeric meaning |
|---|---|
| `light` | brightness % |
| `climate` | target temperature |
| `switch` | (numbers ignored — warning at generation) |
| `fan` | speed % |
| `cover` | position % |
| `media_player` | volume % |
| `input_boolean` | (numbers ignored — warning at generation) |

Other domains (`sensor`, `binary_sensor`, `device_tracker`, etc.) are skipped.

### Excel structure produced

**Sheet `Dispositivos`** (auto-populated, source of truth for entity ids):

| Area | Nombre | Tipo | entity_id | Acepta número |
|---|---|---|---|---|
| Sala | Spots | light | light.sala_spots_xxx | dimming % |
| Sala | A/C | climate | climate.sala_ac_xxx | temperatura |
| Cocina | Luz | light | light.cocina_main_yyy | dimming % |
| Cocina | Enchufe Ventana | switch | switch.cocina_enchufe_zzz | (no) |

`Nombre` defaults to the entity's `friendly_name` stripped of the area prefix when present. The integrator can rename `Nombre` cells as long as `(Area, Nombre)` remains unique.

**Sheets `En Casa`, `Fuera`, `Diario Lun-Vier`** (empty placeholder grids):

- Row 1: area names merged across the area's devices.
- Row 2: device names (`Nombre` column from `Dispositivos`).
- Column A: time slots in 15-minute increments. The Erev-Shabat band (e.g. 18:00–18:45) is visually separated from the rest of the day.
- Cells: empty by default; integrator fills with `ON`/`OFF`/number.

The placeholder sheets get the same column structure for all three sheets (so devices align). If the schedule needs different time ranges per sheet, the integrator can adjust the rows manually.

---

## Component 2: `tools/generate_automations.py`

### Invocation
```
python tools/generate_automations.py path/to/cliente.xlsx \
    --prefix juan \
    --output juan.yaml
```

If `--output` is omitted, prints to stdout.

### Dependencies
- `openpyxl` (read Excel)
- Python 3.11+ (no other requirements)

### Algorithm
1. Load `Dispositivos`. Build map `{(area, nombre): {"type": str, "entity_id": str}}`. Validate uniqueness.
2. For each schedule sheet (`En Casa`, `Fuera`, `Diario Lun-Vier`):
   1. Read row 1 + row 2 to recover `(area, nombre)` per column.
   2. Look up `entity_id` in the map for each column.
   3. For each time row, for each cell with a value:
      - Parse value (`ON`/`OFF`/integer).
      - Determine the action based on `(domain, value)` (see Cell semantics below).
      - Determine condition set based on which sheet and whether the time is in the Erev-Shabat band.
      - Emit one automation entry.
3. Sort automations by `(sheet, time, area, nombre)` for stable diffs.
4. Write YAML.

### Cell semantics

| Cell value | light | climate | switch | fan | cover | media_player | input_boolean |
|---|---|---|---|---|---|---|---|
| `ON` | `light.turn_on` (100%) | `climate.turn_on` | `switch.turn_on` | `fan.turn_on` | `cover.open_cover` | `media_player.turn_on` | `input_boolean.turn_on` |
| `OFF` | `light.turn_off` | `climate.turn_off` | `switch.turn_off` | `fan.turn_off` | `cover.close_cover` | `media_player.turn_off` | `input_boolean.turn_off` |
| Number | `turn_on` w/ `brightness_pct` | `set_temperature` | warn + ignore | `set_percentage` | `set_cover_position` | `volume_set` (0-1 from %) | warn + ignore |

Empty cells, color-only cells, and unrecognised values are skipped silently.

### Sheet → condition mapping

The bands within a sheet decide the trigger window. The "Erev-Shabat band" is rows up to and including the row immediately preceding the regular Shabat block (typically 18:00–18:45 / before 19:00). The script identifies this band by a sentinel header row labelled `Erev Shabat` in column A.

| Sheet + band | Conditions (all AND-joined) |
|---|---|
| `En Casa` (Erev band) | `binary_sensor.dira_shabat_erev_shabbat_hag` is `on` |
| `En Casa` (regular) | `binary_sensor.dira_shabat_issur_melacha` is `on` AND (`dinner_today` is `on` OR `lunch_today` is `on`) |
| `Fuera` (Erev band) | `binary_sensor.dira_shabat_erev_shabbat_hag` is `on` |
| `Fuera` (regular) | `binary_sensor.dira_shabat_issur_melacha` is `on` AND `dinner_today` is `off` AND `lunch_today` is `off` |
| `Diario Lun-Vier` (any) | `binary_sensor.dira_shabat_issur_melacha` is `off` AND `binary_sensor.dira_shabat_erev_shabbat_hag` is `off` AND weekday is Mon–Fri |

The `Diario` sheet uses a weekday filter as part of the condition (Monday through Friday). The `erev_shabbat_hag` check guarantees Friday entries don't fire after candle lighting.

### YAML output format

Stable keys for re-generation: `id: dira_shabat_<prefix>_<NNNN>` (numeric, zero-padded). When the integrator re-runs the generator, the YAML is overwritten and HA replaces the entries by id without duplicates.

```yaml
- id: dira_shabat_juan_0001
  alias: "[Juan · En Casa] Spots Sala → ON @ 19:00"
  trigger:
    - platform: time
      at: "19:00:00"
  condition:
    - condition: state
      entity_id: binary_sensor.dira_shabat_issur_melacha
      state: "on"
    - condition: or
      conditions:
        - condition: state
          entity_id: binary_sensor.dira_shabat_dinner_today
          state: "on"
        - condition: state
          entity_id: binary_sensor.dira_shabat_lunch_today
          state: "on"
  action:
    - service: light.turn_on
      target:
        entity_id: light.sala_spots_xxx
      data:
        brightness_pct: 100
  mode: single
```

Notes on the format:
- `alias` uses `[<Prefix> · <Sheet>] <Nombre> → <Action> @ <HH:MM>` for human readability.
- Each cell is one automation (kept independent for clarity and easier debugging). The integrator can group later via packages if desired.
- All automations include `mode: single` so re-triggers within a window don't stack.

### Error handling

Errors abort generation with a clear message:
- Missing `Dispositivos` sheet.
- Duplicate `(Area, Nombre)` in `Dispositivos`.
- Schedule sheet references an unknown `(Area, Nombre)`.
- Number in a domain that doesn't accept numbers → warning logged, cell skipped.
- Invalid time in column A → warning logged, row skipped.

A summary at the end lists number of automations generated, warnings, and skipped rows.

---

## Out of scope (this iteration)

- Web UI / panel for editing schedules.
- Automatic delivery (the integrator still copies the YAML manually).
- Re-importing YAML back into Excel (one-way: Excel → YAML).
- Per-client `prefix` validation against an existing config; the integrator owns naming.
- Schedule history / audit.

---

## Testing strategy

1. **Unit tests for `generate_automations.py`**:
   - Sample `.xlsx` fixtures covering: simple ON/OFF, dimming numbers, climate temperatures, Erev band, all three sheets, edge cases (unknown nombre, duplicate, bad time, number on switch).
   - Assert the generated YAML matches expected snapshots.

2. **Integration test for `dira_shabat.export_devices`**:
   - With a mocked HA registry containing 2 areas × 3 entity types, calling the service produces an `.xlsx` with the correct `Dispositivos` rows and 3 placeholder sheets.

3. **Manual smoke test on a real instance**:
   - Run `dira_shabat.export_devices` on a real HA → inspect Excel.
   - Fill a few cells across all 3 sheets, run the generator → import YAML into HA → verify automations appear and trigger conditionally.

---

## Files added

- `custom_components/dira_shabat/services.yaml` — declare new service.
- `custom_components/dira_shabat/services.py` (or extend `__init__.py`) — service handler that builds the `.xlsx`.
- `tools/generate_automations.py` — standalone generator.
- `tools/README.md` — usage instructions.
- `tests/tools/test_generate_automations.py` + fixtures (`.xlsx` samples, expected `.yaml`).
