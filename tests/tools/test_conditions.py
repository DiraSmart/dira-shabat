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
