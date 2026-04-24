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
