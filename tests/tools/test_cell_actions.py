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
