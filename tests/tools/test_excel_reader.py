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
