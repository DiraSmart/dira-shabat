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
