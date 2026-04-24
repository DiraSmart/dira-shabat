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
        # End of Erev band: an empty row marks the boundary, then time resumes
        [None, None, None, None],
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
