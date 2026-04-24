# Dira Shabat Scheduler — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Python script `tools/generate_automations.py` that converts a hand-crafted Excel schedule into a Home Assistant automations YAML file using Dira Shabat sensors as conditions.

**Architecture:** Single-purpose script split across a small package (`tools/dira_scheduler/`) with focused modules: `excel_reader` (parse `Dispositivos` + schedule sheets), `cell_actions` (cell value → HA action dict), `conditions` (sheet+band → condition list), `yaml_emitter` (assemble + dump). A thin CLI entrypoint wires everything together. Test-driven with `pytest` + Excel/YAML fixtures.

**Tech Stack:** Python 3.11+, `openpyxl` (Excel reading), `PyYAML` (YAML dump), `pytest` (tests).

**Spec:** [`docs/specs/2026-04-23-scheduler-design.md`](../specs/2026-04-23-scheduler-design.md). Phase 2 (HA service `dira_shabat.export_devices`) is intentionally out of scope.

---

## File structure

```
tools/
├── generate_automations.py        # CLI entrypoint (~30 lines)
├── dira_scheduler/
│   ├── __init__.py                # Package marker
│   ├── cell_actions.py            # cell value → action dict
│   ├── conditions.py              # sheet + band → conditions list
│   ├── excel_reader.py            # parse Dispositivos + schedule sheets
│   └── yaml_emitter.py            # build automation list, dump to YAML
├── requirements.txt               # openpyxl, PyYAML
└── README.md                      # usage instructions

tests/
└── tools/
    ├── __init__.py
    ├── conftest.py                # pytest fixture loader for sample files
    ├── test_cell_actions.py
    ├── test_conditions.py
    ├── test_excel_reader.py
    ├── test_yaml_emitter.py
    ├── test_end_to_end.py
    └── fixtures/
        ├── sample_simple.xlsx     # 1 area, 2 devices, only En Casa
        ├── sample_simple.expected.yaml
        ├── sample_full.xlsx       # multi-area, all 3 sheets, Erev band
        └── sample_full.expected.yaml
```

---

## Task 1: Project skeleton

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/dira_scheduler/__init__.py`
- Create: `tools/requirements.txt`
- Create: `tools/README.md`
- Create: `tests/__init__.py`
- Create: `tests/tools/__init__.py`
- Create: `tests/tools/fixtures/.gitkeep`
- Create: `pytest.ini`

- [ ] **Step 1: Create the package directory tree**

```bash
mkdir -p tools/dira_scheduler tests/tools/fixtures
touch tools/__init__.py tools/dira_scheduler/__init__.py
touch tests/__init__.py tests/tools/__init__.py
touch tests/tools/fixtures/.gitkeep
```

- [ ] **Step 2: Write `tools/requirements.txt`**

```
openpyxl>=3.1
PyYAML>=6.0
pytest>=7.0
```

- [ ] **Step 3: Write `tools/README.md`** (minimal version, expanded later)

```markdown
# Dira Shabat Scheduler — Tools

Generate Home Assistant automations from a per-client Excel schedule.

## Install

```bash
pip install -r tools/requirements.txt
```

## Generate automations

```bash
python tools/generate_automations.py path/to/cliente.xlsx --prefix juan --output juan.yaml
```

See [`docs/specs/2026-04-23-scheduler-design.md`](../docs/specs/2026-04-23-scheduler-design.md) for the Excel format spec.
```

- [ ] **Step 4: Write `pytest.ini`** at repo root

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

- [ ] **Step 5: Install dependencies and verify pytest runs**

```bash
pip install -r tools/requirements.txt
pytest --collect-only
```

Expected: pytest reports 0 tests collected (no failures).

- [ ] **Step 6: Commit**

```bash
git add tools/ tests/ pytest.ini
git commit -m "feat(scheduler): project skeleton (Phase 1)"
```

---

## Task 2: Cell action parser (`cell_actions.py`)

Convert a single cell value (e.g. `"ON"`, `"OFF"`, `30`, `22`, `None`) plus a domain (`light`, `climate`, etc.) into a Home Assistant **action dict** ready to embed in an automation, or `None` if the cell should be skipped.

**Files:**
- Create: `tools/dira_scheduler/cell_actions.py`
- Create: `tests/tools/test_cell_actions.py`

- [ ] **Step 1: Write the failing tests**

Write to `tests/tools/test_cell_actions.py`:

```python
"""Tests for cell value → HA action dict conversion."""
import pytest
from tools.dira_scheduler.cell_actions import parse_cell, UnsupportedNumberWarning

ENTITY = "light.sala_spots"


def test_empty_cell_returns_none():
    assert parse_cell(None, "light", ENTITY) is None
    assert parse_cell("", "light", ENTITY) is None
    assert parse_cell("   ", "light", ENTITY) is None


def test_light_on_returns_full_brightness():
    assert parse_cell("ON", "light", ENTITY) == {
        "service": "light.turn_on",
        "target": {"entity_id": ENTITY},
        "data": {"brightness_pct": 100},
    }


def test_light_off():
    assert parse_cell("OFF", "light", ENTITY) == {
        "service": "light.turn_off",
        "target": {"entity_id": ENTITY},
    }


def test_light_dimming_number():
    assert parse_cell(30, "light", ENTITY) == {
        "service": "light.turn_on",
        "target": {"entity_id": ENTITY},
        "data": {"brightness_pct": 30},
    }


def test_climate_on():
    assert parse_cell("ON", "climate", "climate.sala") == {
        "service": "climate.turn_on",
        "target": {"entity_id": "climate.sala"},
    }


def test_climate_temperature_number():
    assert parse_cell(22, "climate", "climate.sala") == {
        "service": "climate.set_temperature",
        "target": {"entity_id": "climate.sala"},
        "data": {"temperature": 22},
    }


def test_switch_on_off():
    assert parse_cell("ON", "switch", "switch.x")["service"] == "switch.turn_on"
    assert parse_cell("OFF", "switch", "switch.x")["service"] == "switch.turn_off"


def test_switch_number_warns_and_returns_none():
    with pytest.warns(UnsupportedNumberWarning):
        assert parse_cell(50, "switch", "switch.x") is None


def test_input_boolean_number_warns_and_returns_none():
    with pytest.warns(UnsupportedNumberWarning):
        assert parse_cell(50, "input_boolean", "input_boolean.x") is None


def test_fan_number_uses_set_percentage():
    assert parse_cell(75, "fan", "fan.x") == {
        "service": "fan.set_percentage",
        "target": {"entity_id": "fan.x"},
        "data": {"percentage": 75},
    }


def test_cover_on_off_open_close():
    assert parse_cell("ON", "cover", "cover.x")["service"] == "cover.open_cover"
    assert parse_cell("OFF", "cover", "cover.x")["service"] == "cover.close_cover"


def test_cover_number_uses_set_position():
    assert parse_cell(40, "cover", "cover.x") == {
        "service": "cover.set_cover_position",
        "target": {"entity_id": "cover.x"},
        "data": {"position": 40},
    }


def test_media_player_number_uses_volume_set():
    assert parse_cell(50, "media_player", "media_player.x") == {
        "service": "media_player.volume_set",
        "target": {"entity_id": "media_player.x"},
        "data": {"volume_level": 0.5},
    }


def test_case_insensitive_on_off():
    assert parse_cell("on", "light", ENTITY)["service"] == "light.turn_on"
    assert parse_cell("Off", "light", ENTITY)["service"] == "light.turn_off"


def test_unknown_value_returns_none():
    assert parse_cell("MAYBE", "light", ENTITY) is None
    assert parse_cell("foo", "switch", "switch.x") is None


def test_unknown_domain_returns_none():
    assert parse_cell("ON", "sensor", "sensor.x") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tools/test_cell_actions.py -v
```

Expected: ImportError / module not found.

- [ ] **Step 3: Implement `cell_actions.py`**

Write to `tools/dira_scheduler/cell_actions.py`:

```python
"""Convert a single Excel cell value into a Home Assistant action dict."""
from __future__ import annotations

import warnings
from typing import Any


class UnsupportedNumberWarning(UserWarning):
    """Raised when a number is placed in a cell whose domain ignores numbers."""


_ON = {"on", "ON", "On"}
_OFF = {"off", "OFF", "Off"}


def parse_cell(value: Any, domain: str, entity_id: str) -> dict | None:
    """Return the HA action dict for this cell, or None if it should be skipped.

    Empty cells, color-only cells, and unrecognised values return None.
    Numbers in domains that don't accept numbers (switch, input_boolean) emit
    an UnsupportedNumberWarning and return None.
    """
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.lower() == "on":
            return _on_action(domain, entity_id)
        if stripped.lower() == "off":
            return _off_action(domain, entity_id)
        # Try to coerce numeric strings ("30") to int
        try:
            return _number_action(int(stripped), domain, entity_id)
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        return _number_action(int(value), domain, entity_id)
    return None


def _on_action(domain: str, entity_id: str) -> dict | None:
    if domain == "light":
        return {
            "service": "light.turn_on",
            "target": {"entity_id": entity_id},
            "data": {"brightness_pct": 100},
        }
    if domain == "cover":
        return {
            "service": "cover.open_cover",
            "target": {"entity_id": entity_id},
        }
    if domain in {"climate", "switch", "fan", "media_player", "input_boolean"}:
        return {
            "service": f"{domain}.turn_on",
            "target": {"entity_id": entity_id},
        }
    return None


def _off_action(domain: str, entity_id: str) -> dict | None:
    if domain == "cover":
        return {
            "service": "cover.close_cover",
            "target": {"entity_id": entity_id},
        }
    if domain in {"light", "climate", "switch", "fan", "media_player", "input_boolean"}:
        return {
            "service": f"{domain}.turn_off",
            "target": {"entity_id": entity_id},
        }
    return None


def _number_action(n: int, domain: str, entity_id: str) -> dict | None:
    if domain == "light":
        return {
            "service": "light.turn_on",
            "target": {"entity_id": entity_id},
            "data": {"brightness_pct": n},
        }
    if domain == "climate":
        return {
            "service": "climate.set_temperature",
            "target": {"entity_id": entity_id},
            "data": {"temperature": n},
        }
    if domain == "fan":
        return {
            "service": "fan.set_percentage",
            "target": {"entity_id": entity_id},
            "data": {"percentage": n},
        }
    if domain == "cover":
        return {
            "service": "cover.set_cover_position",
            "target": {"entity_id": entity_id},
            "data": {"position": n},
        }
    if domain == "media_player":
        return {
            "service": "media_player.volume_set",
            "target": {"entity_id": entity_id},
            "data": {"volume_level": round(n / 100, 2)},
        }
    if domain in {"switch", "input_boolean"}:
        warnings.warn(
            f"Number value '{n}' on entity '{entity_id}' (domain '{domain}') "
            "is not supported; cell skipped.",
            UnsupportedNumberWarning,
            stacklevel=3,
        )
        return None
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_cell_actions.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/dira_scheduler/cell_actions.py tests/tools/test_cell_actions.py
git commit -m "feat(scheduler): cell value to HA action parser"
```

---

## Task 3: Condition builder (`conditions.py`)

Build the list of HA condition dicts for an automation, given the sheet name and whether the time is in the Erev-Shabat band.

**Files:**
- Create: `tools/dira_scheduler/conditions.py`
- Create: `tests/tools/test_conditions.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for sheet+band → HA condition list."""
import pytest
from tools.dira_scheduler.conditions import build_conditions, UnknownSheetError


def test_en_casa_regular():
    assert build_conditions("En Casa", in_erev_band=False) == [
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_issur_melacha",
            "state": "on",
        },
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "binary_sensor.dira_shabat_dinner_today",
                    "state": "on",
                },
                {
                    "condition": "state",
                    "entity_id": "binary_sensor.dira_shabat_lunch_today",
                    "state": "on",
                },
            ],
        },
    ]


def test_en_casa_erev():
    assert build_conditions("En Casa", in_erev_band=True) == [
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_erev_shabbat_hag",
            "state": "on",
        },
    ]


def test_fuera_regular():
    assert build_conditions("Fuera", in_erev_band=False) == [
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_issur_melacha",
            "state": "on",
        },
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_dinner_today",
            "state": "off",
        },
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_lunch_today",
            "state": "off",
        },
    ]


def test_fuera_erev_same_as_en_casa_erev():
    assert build_conditions("Fuera", in_erev_band=True) == [
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_erev_shabbat_hag",
            "state": "on",
        },
    ]


def test_diario_lun_vier():
    expected = [
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_issur_melacha",
            "state": "off",
        },
        {
            "condition": "state",
            "entity_id": "binary_sensor.dira_shabat_erev_shabbat_hag",
            "state": "off",
        },
        {
            "condition": "time",
            "weekday": ["mon", "tue", "wed", "thu", "fri"],
        },
    ]
    assert build_conditions("Diario Lun-Vier", in_erev_band=False) == expected
    # Erev band is irrelevant for Diario sheet; still returns the same conditions
    assert build_conditions("Diario Lun-Vier", in_erev_band=True) == expected


def test_unknown_sheet_raises():
    with pytest.raises(UnknownSheetError, match="Otra"):
        build_conditions("Otra", in_erev_band=False)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tools/test_conditions.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `conditions.py`**

```python
"""Map a (sheet, band) pair to the HA condition list for an automation."""
from __future__ import annotations


class UnknownSheetError(ValueError):
    """Raised when a schedule sheet has an unrecognised name."""


_ISSUR = "binary_sensor.dira_shabat_issur_melacha"
_EREV = "binary_sensor.dira_shabat_erev_shabbat_hag"
_DINNER = "binary_sensor.dira_shabat_dinner_today"
_LUNCH = "binary_sensor.dira_shabat_lunch_today"


def _state(entity_id: str, state: str) -> dict:
    return {"condition": "state", "entity_id": entity_id, "state": state}


def build_conditions(sheet: str, in_erev_band: bool) -> list[dict]:
    """Return the HA condition list for cells on this sheet+band."""
    if sheet == "En Casa":
        if in_erev_band:
            return [_state(_EREV, "on")]
        return [
            _state(_ISSUR, "on"),
            {
                "condition": "or",
                "conditions": [_state(_DINNER, "on"), _state(_LUNCH, "on")],
            },
        ]
    if sheet == "Fuera":
        if in_erev_band:
            return [_state(_EREV, "on")]
        return [
            _state(_ISSUR, "on"),
            _state(_DINNER, "off"),
            _state(_LUNCH, "off"),
        ]
    if sheet == "Diario Lun-Vier":
        return [
            _state(_ISSUR, "off"),
            _state(_EREV, "off"),
            {"condition": "time", "weekday": ["mon", "tue", "wed", "thu", "fri"]},
        ]
    raise UnknownSheetError(f"Unknown schedule sheet: {sheet!r}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_conditions.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/dira_scheduler/conditions.py tests/tools/test_conditions.py
git commit -m "feat(scheduler): sheet+band condition builder"
```

---

## Task 4: Excel reader — Dispositivos sheet

Parse the `Dispositivos` sheet into a `Device` dataclass list and an `(Area, Nombre) → Device` lookup map. Raise on duplicates and unknown domains.

**Files:**
- Create: `tools/dira_scheduler/excel_reader.py`
- Create: `tests/tools/test_excel_reader.py`
- Create: `tests/tools/conftest.py`

- [ ] **Step 1: Write `conftest.py`** to share an Excel-builder helper

```python
"""Shared fixtures: tiny in-memory Excel builder for tests."""
from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook


@pytest.fixture
def make_xlsx(tmp_path):
    """Return a builder: pass a dict {sheet: rows}, get back an .xlsx Path."""
    def _build(sheets: dict[str, list[list]]) -> BytesIO | str:
        wb = Workbook()
        wb.remove(wb.active)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            for row in rows:
                ws.append(row)
        path = tmp_path / "test.xlsx"
        wb.save(path)
        return path
    return _build
```

- [ ] **Step 2: Write the failing tests**

```python
"""Tests for parsing the Dispositivos sheet."""
import pytest

from tools.dira_scheduler.excel_reader import (
    Device,
    DispositivosError,
    read_dispositivos,
)


def test_reads_basic_devices(make_xlsx):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
            ["Sala", "A/C", "climate", "climate.sala_ac", "temperatura"],
            ["Cocina", "Luz", "light", "light.cocina", "dimming %"],
        ],
    })
    devices = read_dispositivos(path)
    assert devices[("Sala", "Spots")] == Device(
        area="Sala", nombre="Spots", domain="light",
        entity_id="light.sala_spots",
    )
    assert devices[("Sala", "A/C")].domain == "climate"
    assert devices[("Cocina", "Luz")].entity_id == "light.cocina"
    assert len(devices) == 3


def test_missing_sheet_raises(make_xlsx):
    path = make_xlsx({"Otra": [["foo"]]})
    with pytest.raises(DispositivosError, match="Dispositivos"):
        read_dispositivos(path)


def test_duplicate_area_nombre_raises(make_xlsx):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.x", ""],
            ["Sala", "Spots", "light", "light.y", ""],
        ],
    })
    with pytest.raises(DispositivosError, match="duplicate"):
        read_dispositivos(path)


def test_unknown_domain_raises(make_xlsx):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Sensor", "sensor", "sensor.x", ""],
        ],
    })
    with pytest.raises(DispositivosError, match="domain"):
        read_dispositivos(path)


def test_blank_rows_are_skipped(make_xlsx):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
            [None, None, None, None, None],
            ["", "", "", "", ""],
            ["Cocina", "Luz", "light", "light.cocina", "dimming %"],
        ],
    })
    devices = read_dispositivos(path)
    assert len(devices) == 2
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/tools/test_excel_reader.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `excel_reader.py` (Dispositivos part only)**

```python
"""Parse Dira Shabat scheduler Excel files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from openpyxl import load_workbook


SUPPORTED_DOMAINS = frozenset({
    "light", "climate", "switch", "fan",
    "cover", "media_player", "input_boolean",
})


class DispositivosError(ValueError):
    """Raised when the Dispositivos sheet is missing or malformed."""


@dataclass(frozen=True)
class Device:
    area: str
    nombre: str
    domain: str
    entity_id: str


def read_dispositivos(path: str | Path) -> dict[tuple[str, str], Device]:
    """Load the Dispositivos sheet into an (Area, Nombre) → Device map."""
    wb = load_workbook(path, read_only=True, data_only=True)
    if "Dispositivos" not in wb.sheetnames:
        raise DispositivosError("Sheet 'Dispositivos' is missing from the workbook")
    ws = wb["Dispositivos"]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise DispositivosError("Sheet 'Dispositivos' is empty")
    # Skip header row
    out: dict[tuple[str, str], Device] = {}
    for idx, row in enumerate(rows[1:], start=2):
        area, nombre, tipo, entity_id, *_ = (list(row) + [None] * 5)[:5]
        if not any((area, nombre, tipo, entity_id)):
            continue  # blank row
        if not (area and nombre and tipo and entity_id):
            raise DispositivosError(
                f"Row {idx} in Dispositivos has missing required field"
            )
        area, nombre, tipo, entity_id = (
            str(area).strip(), str(nombre).strip(),
            str(tipo).strip(), str(entity_id).strip(),
        )
        if tipo not in SUPPORTED_DOMAINS:
            raise DispositivosError(
                f"Row {idx}: unknown domain '{tipo}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_DOMAINS))}"
            )
        key = (area, nombre)
        if key in out:
            raise DispositivosError(
                f"Row {idx}: duplicate (Area, Nombre) entry: {key}"
            )
        out[key] = Device(area=area, nombre=nombre, domain=tipo, entity_id=entity_id)
    return out
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/tools/test_excel_reader.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 6: Commit**

```bash
git add tools/dira_scheduler/excel_reader.py tests/tools/test_excel_reader.py tests/tools/conftest.py
git commit -m "feat(scheduler): Dispositivos sheet reader"
```

---

## Task 5: Excel reader — Schedule sheets

Add `read_schedule_sheet()` that returns an iterable of `(time, in_erev_band, area, nombre, raw_value)` tuples for one schedule sheet.

**Files:**
- Modify: `tools/dira_scheduler/excel_reader.py` (add new function)
- Modify: `tests/tools/test_excel_reader.py` (add new tests)

- [ ] **Step 1: Write the failing tests** (append to `test_excel_reader.py`)

```python
from tools.dira_scheduler.excel_reader import (
    ScheduleCell,
    read_schedule_sheet,
)


def _schedule_sheet_rows():
    """Sample rows: row 1 = areas, row 2 = nombres, col A = times."""
    return [
        # Row 1: area headers (col A blank, then areas spanning their columns)
        [None, "Sala", "Sala", "Cocina"],
        # Row 2: nombre headers
        [None, "Spots", "A/C", "Luz"],
        # Erev band sentinel
        ["Erev Shabat", None, None, None],
        # Erev band time slots
        ["18:00", "ON", None, None],
        ["18:30", None, "22", None],
        # End of Erev band: any non-time row marks the boundary, here an empty row + time resumes
        # Regular section
        ["19:00", None, None, "ON"],
        ["20:00", "30", None, None],
    ]


def test_read_schedule_basic(make_xlsx):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
        ],
        "En Casa": _schedule_sheet_rows(),
    })
    cells = list(read_schedule_sheet(path, "En Casa"))
    assert ScheduleCell(time="18:00", in_erev_band=True, area="Sala",
                       nombre="Spots", value="ON") in cells
    assert ScheduleCell(time="18:30", in_erev_band=True, area="Sala",
                       nombre="A/C", value=22) in cells
    assert ScheduleCell(time="19:00", in_erev_band=False, area="Cocina",
                       nombre="Luz", value="ON") in cells
    assert ScheduleCell(time="20:00", in_erev_band=False, area="Sala",
                       nombre="Spots", value=30) in cells
    # No empty cells should appear
    assert len(cells) == 4


def test_schedule_sheet_without_erev_band(make_xlsx):
    """Schedule with no 'Erev Shabat' sentinel: nothing is in erev band."""
    path = make_xlsx({
        "Dispositivos": [["Area", "Nombre", "Tipo", "entity_id", "Acepta número"]],
        "Diario Lun-Vier": [
            [None, "Sala"],
            [None, "Spots"],
            ["07:00", "ON"],
            ["22:00", "OFF"],
        ],
    })
    cells = list(read_schedule_sheet(path, "Diario Lun-Vier"))
    assert all(not c.in_erev_band for c in cells)
    assert len(cells) == 2


def test_missing_schedule_sheet_returns_empty(make_xlsx):
    """A sheet that doesn't exist yields nothing (not all clients use all 3)."""
    path = make_xlsx({
        "Dispositivos": [["Area", "Nombre", "Tipo", "entity_id", "Acepta número"]],
    })
    assert list(read_schedule_sheet(path, "Fuera")) == []


def test_time_parsed_from_datetime_object(make_xlsx):
    """openpyxl returns datetime.time for hh:mm cells; we accept that too."""
    from datetime import time as dt_time
    path = make_xlsx({
        "Dispositivos": [["Area", "Nombre", "Tipo", "entity_id", "Acepta número"]],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            [dt_time(19, 0), "ON"],
        ],
    })
    cells = list(read_schedule_sheet(path, "En Casa"))
    assert cells[0].time == "19:00"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tools/test_excel_reader.py::test_read_schedule_basic -v
```

Expected: ImportError on `ScheduleCell` / `read_schedule_sheet`.

- [ ] **Step 3: Extend `excel_reader.py`** — append at the end:

```python
from datetime import time as _dt_time
from typing import Iterator


@dataclass(frozen=True)
class ScheduleCell:
    time: str               # "HH:MM"
    in_erev_band: bool
    area: str
    nombre: str
    value: str | int


_EREV_SENTINEL = "erev shabat"


def _format_time(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, _dt_time):
        return value.strftime("%H:%M")
    s = str(value).strip()
    if not s:
        return None
    # Accept "HH:MM" (allow single-digit hour)
    parts = s.split(":")
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= h < 24 and 0 <= m < 60):
        return None
    return f"{h:02d}:{m:02d}"


def read_schedule_sheet(path: str | Path, sheet_name: str) -> Iterator[ScheduleCell]:
    """Yield ScheduleCell for every non-empty cell in a schedule sheet.

    Returns nothing if the sheet doesn't exist.
    Row 1 = area headers (col A blank), row 2 = nombre headers.
    Column A is times; a row with col A == 'Erev Shabat' (case-insensitive)
    starts the Erev band; the band ends on the next row whose col A is empty
    or non-time.
    """
    wb = load_workbook(path, read_only=True, data_only=True)
    if sheet_name not in wb.sheetnames:
        return
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 3:
        return

    # Build column → (area, nombre) mapping
    area_row = list(rows[0])
    nombre_row = list(rows[1])
    col_map: dict[int, tuple[str, str]] = {}
    last_area: str | None = None
    for col_idx, area in enumerate(area_row):
        if col_idx == 0:
            continue
        if area is not None:
            last_area = str(area).strip() or last_area
        nombre = nombre_row[col_idx] if col_idx < len(nombre_row) else None
        if last_area and nombre:
            col_map[col_idx] = (last_area, str(nombre).strip())

    in_erev = False
    for row in rows[2:]:
        col_a = row[0]
        if col_a is not None and str(col_a).strip().lower() == _EREV_SENTINEL:
            in_erev = True
            continue
        time = _format_time(col_a)
        if time is None:
            in_erev = False  # band ends at first non-time row after entering
            continue
        for col_idx, (area, nombre) in col_map.items():
            if col_idx >= len(row):
                continue
            value = row[col_idx]
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            yield ScheduleCell(
                time=time,
                in_erev_band=in_erev,
                area=area,
                nombre=nombre,
                value=value if isinstance(value, (int, float)) else str(value).strip(),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_excel_reader.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/dira_scheduler/excel_reader.py tests/tools/test_excel_reader.py
git commit -m "feat(scheduler): schedule sheet reader with Erev-band detection"
```

---

## Task 6: YAML emitter (`yaml_emitter.py`)

Combine devices + schedule cells + conditions to produce the final list of automation dicts and serialize to a YAML string.

**Files:**
- Create: `tools/dira_scheduler/yaml_emitter.py`
- Create: `tests/tools/test_yaml_emitter.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for assembling automations and dumping YAML."""
import yaml

from tools.dira_scheduler.excel_reader import Device, ScheduleCell
from tools.dira_scheduler.yaml_emitter import (
    build_automations,
    dump_yaml,
)


def _devices():
    return {
        ("Sala", "Spots"): Device("Sala", "Spots", "light", "light.sala_spots"),
        ("Sala", "A/C"): Device("Sala", "A/C", "climate", "climate.sala_ac"),
    }


def _cells():
    return [
        ScheduleCell("19:00", False, "Sala", "Spots", "ON"),
        ScheduleCell("23:00", False, "Sala", "A/C", "OFF"),
        ScheduleCell("18:00", True, "Sala", "A/C", 22),
    ]


def test_build_automations_emits_one_per_cell():
    automations = build_automations(
        cells_by_sheet={"En Casa": _cells()},
        devices=_devices(),
        prefix="juan",
    )
    assert len(automations) == 3


def test_automation_has_stable_id():
    automations = build_automations(
        cells_by_sheet={"En Casa": _cells()},
        devices=_devices(),
        prefix="juan",
    )
    ids = [a["id"] for a in automations]
    assert ids == ["dira_shabat_juan_0001", "dira_shabat_juan_0002", "dira_shabat_juan_0003"]


def test_automation_has_human_alias():
    automations = build_automations(
        cells_by_sheet={"En Casa": [ScheduleCell("19:00", False, "Sala", "Spots", "ON")]},
        devices=_devices(),
        prefix="juan",
    )
    assert automations[0]["alias"] == "[Juan · En Casa] Spots Sala → ON @ 19:00"


def test_automation_full_structure():
    automations = build_automations(
        cells_by_sheet={"En Casa": [ScheduleCell("19:00", False, "Sala", "Spots", "ON")]},
        devices=_devices(),
        prefix="juan",
    )
    a = automations[0]
    assert a["trigger"] == [{"platform": "time", "at": "19:00:00"}]
    assert a["mode"] == "single"
    assert a["action"][0]["service"] == "light.turn_on"
    # Conditions come from conditions.build_conditions
    assert any(
        c.get("entity_id") == "binary_sensor.dira_shabat_issur_melacha"
        for c in a["condition"]
    )


def test_unknown_device_skips_with_warning(recwarn):
    cells = [ScheduleCell("19:00", False, "Sala", "MissingThing", "ON")]
    automations = build_automations(
        cells_by_sheet={"En Casa": cells},
        devices=_devices(),
        prefix="juan",
    )
    assert automations == []
    assert any("MissingThing" in str(w.message) for w in recwarn.list)


def test_sort_order_stable(make_xlsx):
    """Automations sorted by (sheet, time, area, nombre) for stable diffs."""
    cells = {
        "Fuera": [ScheduleCell("19:00", False, "Sala", "Spots", "OFF")],
        "En Casa": [
            ScheduleCell("19:00", False, "Sala", "Spots", "ON"),
            ScheduleCell("18:00", True, "Sala", "Spots", "OFF"),
        ],
    }
    automations = build_automations(cells, _devices(), prefix="x")
    times_and_sheets = [(a["alias"], a["id"]) for a in automations]
    # En Casa rows come before Fuera rows; within En Casa, 18:00 before 19:00
    assert "En Casa" in automations[0]["alias"]
    assert "@ 18:00" in automations[0]["alias"]
    assert "En Casa" in automations[1]["alias"]
    assert "@ 19:00" in automations[1]["alias"]
    assert "Fuera" in automations[2]["alias"]


def test_dump_yaml_round_trips():
    automations = build_automations(
        cells_by_sheet={"En Casa": [ScheduleCell("19:00", False, "Sala", "Spots", "ON")]},
        devices=_devices(),
        prefix="juan",
    )
    out = dump_yaml(automations)
    parsed = yaml.safe_load(out)
    assert parsed == automations
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tools/test_yaml_emitter.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `yaml_emitter.py`**

```python
"""Assemble HA automations from parsed Excel data and serialize to YAML."""
from __future__ import annotations

import warnings
from typing import Iterable

import yaml

from tools.dira_scheduler.cell_actions import parse_cell
from tools.dira_scheduler.conditions import build_conditions
from tools.dira_scheduler.excel_reader import Device, ScheduleCell


_SHEET_ORDER = ("En Casa", "Fuera", "Diario Lun-Vier")


def build_automations(
    cells_by_sheet: dict[str, Iterable[ScheduleCell]],
    devices: dict[tuple[str, str], Device],
    prefix: str,
) -> list[dict]:
    """Build the full automation list for all sheets."""
    rows: list[tuple[int, str, ScheduleCell, dict]] = []
    for sheet in _SHEET_ORDER:
        cells = cells_by_sheet.get(sheet, [])
        for cell in cells:
            device = devices.get((cell.area, cell.nombre))
            if device is None:
                warnings.warn(
                    f"Sheet {sheet!r} references unknown device "
                    f"({cell.area!r}, {cell.nombre!r}); cell skipped.",
                    UserWarning,
                    stacklevel=2,
                )
                continue
            action = parse_cell(cell.value, device.domain, device.entity_id)
            if action is None:
                continue
            rows.append((
                _SHEET_ORDER.index(sheet),
                sheet,
                cell,
                action,
            ))
    # Stable sort: by (sheet_idx, time, area, nombre)
    rows.sort(key=lambda r: (r[0], r[2].time, r[2].area, r[2].nombre))

    out = []
    for n, (_sheet_idx, sheet, cell, action) in enumerate(rows, start=1):
        out.append(_build_one(prefix, n, sheet, cell, action))
    return out


def _build_one(prefix: str, n: int, sheet: str, cell: ScheduleCell, action: dict) -> dict:
    return {
        "id": f"dira_shabat_{prefix}_{n:04d}",
        "alias": _alias(prefix, sheet, cell),
        "trigger": [{"platform": "time", "at": f"{cell.time}:00"}],
        "condition": build_conditions(sheet, cell.in_erev_band),
        "action": [action],
        "mode": "single",
    }


def _alias(prefix: str, sheet: str, cell: ScheduleCell) -> str:
    verb = _verb_for_value(cell.value)
    return (
        f"[{prefix.capitalize()} · {sheet}] "
        f"{cell.nombre} {cell.area} → {verb} @ {cell.time}"
    )


def _verb_for_value(value) -> str:
    if isinstance(value, (int, float)):
        return f"{int(value)}"
    return str(value).upper()


def dump_yaml(automations: list[dict]) -> str:
    """Serialize the automation list as a YAML string."""
    return yaml.safe_dump(
        automations,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_yaml_emitter.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/dira_scheduler/yaml_emitter.py tests/tools/test_yaml_emitter.py
git commit -m "feat(scheduler): YAML emitter for automations"
```

---

## Task 7: CLI entrypoint (`generate_automations.py`)

Wire the modules into a CLI: read Dispositivos + each schedule sheet, build automations, write YAML to stdout or `--output` file.

**Files:**
- Create: `tools/generate_automations.py`
- Create: `tests/tools/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for the CLI entrypoint."""
import sys
import subprocess
from pathlib import Path

import pytest
import yaml


def _run(args, cwd):
    result = subprocess.run(
        [sys.executable, "tools/generate_automations.py", *args],
        capture_output=True, text=True, cwd=cwd,
    )
    return result


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent.parent


def test_cli_writes_to_stdout_when_no_output(make_xlsx, repo_root):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
        ],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            ["19:00", "ON"],
        ],
    })
    result = _run([str(path), "--prefix", "juan"], cwd=repo_root)
    assert result.returncode == 0, result.stderr
    parsed = yaml.safe_load(result.stdout)
    assert len(parsed) == 1
    assert parsed[0]["id"] == "dira_shabat_juan_0001"


def test_cli_writes_to_output_file(make_xlsx, tmp_path, repo_root):
    src = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
        ],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            ["19:00", "ON"],
        ],
    })
    out = tmp_path / "out.yaml"
    result = _run(
        [str(src), "--prefix", "juan", "--output", str(out)],
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stderr
    parsed = yaml.safe_load(out.read_text())
    assert parsed[0]["alias"].startswith("[Juan")


def test_cli_exits_nonzero_on_missing_dispositivos(make_xlsx, repo_root):
    path = make_xlsx({"En Casa": [["foo"]]})
    result = _run([str(path), "--prefix", "juan"], cwd=repo_root)
    assert result.returncode != 0
    assert "Dispositivos" in result.stderr


def test_cli_summary_to_stderr(make_xlsx, repo_root):
    path = make_xlsx({
        "Dispositivos": [
            ["Area", "Nombre", "Tipo", "entity_id", "Acepta número"],
            ["Sala", "Spots", "light", "light.sala_spots", "dimming %"],
        ],
        "En Casa": [
            [None, "Sala"],
            [None, "Spots"],
            ["19:00", "ON"],
            ["20:00", "OFF"],
        ],
    })
    result = _run([str(path), "--prefix", "juan"], cwd=repo_root)
    assert result.returncode == 0
    assert "2 automation" in result.stderr.lower() or "2 automations" in result.stderr.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/tools/test_cli.py -v
```

Expected: subprocess returns non-zero (`generate_automations.py` doesn't exist).

- [ ] **Step 3: Implement `tools/generate_automations.py`**

```python
"""CLI: convert a Dira Shabat scheduler Excel into HA automations YAML."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.dira_scheduler.excel_reader import (  # noqa: E402
    DispositivosError,
    read_dispositivos,
    read_schedule_sheet,
)
from tools.dira_scheduler.yaml_emitter import (  # noqa: E402
    build_automations,
    dump_yaml,
)


SHEETS = ("En Casa", "Fuera", "Diario Lun-Vier")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the client's .xlsx schedule")
    parser.add_argument("--prefix", required=True, help="Client identifier (used in automation ids/aliases)")
    parser.add_argument("--output", help="Write YAML to this file instead of stdout")
    args = parser.parse_args(argv)

    src = Path(args.input)
    if not src.is_file():
        print(f"Error: input file not found: {src}", file=sys.stderr)
        return 2

    try:
        devices = read_dispositivos(src)
    except DispositivosError as err:
        print(f"Error reading Dispositivos: {err}", file=sys.stderr)
        return 1

    cells_by_sheet = {sheet: list(read_schedule_sheet(src, sheet)) for sheet in SHEETS}
    automations = build_automations(cells_by_sheet, devices, prefix=args.prefix)
    yaml_text = dump_yaml(automations)

    if args.output:
        Path(args.output).write_text(yaml_text, encoding="utf-8")
    else:
        sys.stdout.write(yaml_text)

    print(f"Generated {len(automations)} automations.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_cli.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/generate_automations.py tests/tools/test_cli.py
git commit -m "feat(scheduler): CLI entrypoint"
```

---

## Task 8: End-to-end fixture test

A fully realistic Excel + expected YAML pair, executed via the CLI to lock in the YAML format. This is the test you re-run after any future change to catch regressions.

**Files:**
- Create: `tests/tools/fixtures/sample_full.xlsx` (built by a fixture script)
- Create: `tests/tools/fixtures/sample_full.expected.yaml` (regenerated and committed)
- Create: `tests/tools/test_end_to_end.py`

- [ ] **Step 1: Write a script to build the fixture xlsx**

Create `tests/tools/fixtures/_build_sample_full.py`:

```python
"""Run once to (re)create sample_full.xlsx."""
from pathlib import Path

from openpyxl import Workbook


def build():
    wb = Workbook()
    wb.remove(wb.active)

    disp = wb.create_sheet("Dispositivos")
    disp.append(["Area", "Nombre", "Tipo", "entity_id", "Acepta número"])
    disp.append(["Sala", "Spots", "light", "light.sala_spots", "dimming %"])
    disp.append(["Sala", "A/C", "climate", "climate.sala_ac", "temperatura"])
    disp.append(["Cocina", "Luz", "light", "light.cocina_main", "dimming %"])

    encasa = wb.create_sheet("En Casa")
    encasa.append([None, "Sala", "Sala", "Cocina"])
    encasa.append([None, "Spots", "A/C", "Luz"])
    encasa.append(["Erev Shabat", None, None, None])
    encasa.append(["18:00", "ON", None, None])
    encasa.append(["18:30", None, 22, None])
    encasa.append(["19:00", None, None, "ON"])
    encasa.append(["20:00", 30, None, None])
    encasa.append(["23:00", "OFF", "OFF", "OFF"])

    fuera = wb.create_sheet("Fuera")
    fuera.append([None, "Cocina"])
    fuera.append([None, "Luz"])
    fuera.append(["19:00", "ON"])
    fuera.append(["23:00", "OFF"])

    diario = wb.create_sheet("Diario Lun-Vier")
    diario.append([None, "Sala"])
    diario.append([None, "Spots"])
    diario.append(["07:00", "ON"])
    diario.append(["22:30", "OFF"])

    out = Path(__file__).parent / "sample_full.xlsx"
    wb.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Generate the fixture**

```bash
python tests/tools/fixtures/_build_sample_full.py
```

Expected: prints `wrote .../sample_full.xlsx` and the file appears.

- [ ] **Step 3: Generate the expected YAML once and commit it**

```bash
python tools/generate_automations.py tests/tools/fixtures/sample_full.xlsx \
    --prefix sample > tests/tools/fixtures/sample_full.expected.yaml
```

Open `sample_full.expected.yaml` and verify the output looks correct (correct ids, conditions per sheet, action per domain, time order). If wrong, fix the bug and regenerate.

- [ ] **Step 4: Write the end-to-end test**

`tests/tools/test_end_to_end.py`:

```python
"""End-to-end fixture test that locks in the YAML output."""
import subprocess
import sys
from pathlib import Path

import yaml


FIXTURES = Path(__file__).parent / "fixtures"


def test_full_fixture_matches_expected(tmp_path):
    src = FIXTURES / "sample_full.xlsx"
    expected = yaml.safe_load((FIXTURES / "sample_full.expected.yaml").read_text())
    out_file = tmp_path / "out.yaml"
    repo_root = Path(__file__).resolve().parent.parent.parent
    result = subprocess.run(
        [
            sys.executable, "tools/generate_automations.py",
            str(src), "--prefix", "sample", "--output", str(out_file),
        ],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result.returncode == 0, result.stderr
    actual = yaml.safe_load(out_file.read_text())
    assert actual == expected
```

- [ ] **Step 5: Run the e2e test**

```bash
pytest tests/tools/test_end_to_end.py -v
```

Expected: PASS. If it fails because the expected YAML wasn't generated correctly, fix it and regenerate (Step 3).

- [ ] **Step 6: Commit**

```bash
git add tests/tools/fixtures/_build_sample_full.py \
        tests/tools/fixtures/sample_full.xlsx \
        tests/tools/fixtures/sample_full.expected.yaml \
        tests/tools/test_end_to_end.py
git commit -m "test(scheduler): end-to-end fixture lock"
```

---

## Task 9: README with full usage walkthrough

Replace the minimal README with the actual user-facing instructions.

**Files:**
- Modify: `tools/README.md`

- [ ] **Step 1: Rewrite `tools/README.md`**

```markdown
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
```

- [ ] **Step 2: Verify all tests still pass after README changes**

```bash
pytest -v
```

Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add tools/README.md
git commit -m "docs(scheduler): full usage walkthrough"
```

---

## Task 10: Smoke test on a real instance (manual)

This isn't a coded step — it's the validation for Phase 1 to call it done.

- [ ] **Step 1: Build a tiny realistic Excel**

Manually create an `.xlsx` for one of your clients with 2-3 real devices and a handful of schedule entries.

- [ ] **Step 2: Generate the YAML**

```bash
python tools/generate_automations.py tu_cliente.xlsx --prefix tu_cliente > tu_cliente.yaml
```

- [ ] **Step 3: Inspect the YAML**

Open `tu_cliente.yaml` and check:
- Each entry has unique `id` `dira_shabat_<prefix>_NNNN`.
- Conditions match the sheet (Erev sensor for Erev band, issur+meals for En Casa regular, etc.).
- Actions reference the correct entity_ids.
- Time triggers in `HH:MM:00` format.

- [ ] **Step 4: Paste into client's HA**

Copy the YAML into `automations.yaml` (or as a package file under `/config/packages/`). Reload automations from HA UI.

- [ ] **Step 5: Force-trigger one automation to confirm**

In Developer Tools → States, manually set the relevant `binary_sensor.dira_shabat_*` entities to satisfy the conditions, then watch the action fire at the trigger time (or use Run Now from the UI).

If something doesn't behave as expected:
- Open an issue describing the cell, expected behavior, observed behavior.
- We tweak the script (likely the YAML format or condition list) and re-run the e2e fixture test.

When this manual smoke test passes for at least one real client, **Phase 1 is done** and we move to Phase 2 (the `dira_shabat.export_devices` HA service).
