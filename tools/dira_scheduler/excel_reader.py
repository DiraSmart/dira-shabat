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
    """Load the Dispositivos sheet into an (Area, Nombre) -> Device map."""
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
