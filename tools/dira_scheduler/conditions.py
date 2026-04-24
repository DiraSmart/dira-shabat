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
