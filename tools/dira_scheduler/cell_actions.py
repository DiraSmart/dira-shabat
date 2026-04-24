"""Convert a single Excel cell value into a Home Assistant action dict."""
from __future__ import annotations

import warnings
from typing import Any


class UnsupportedNumberWarning(UserWarning):
    """Raised when a number is placed in a cell whose domain ignores numbers."""


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
        # Try to coerce numeric strings: int first, then float
        try:
            return _number_action(int(stripped), domain, entity_id)
        except ValueError:
            try:
                return _number_action(float(stripped), domain, entity_id)
            except ValueError:
                return None
    if isinstance(value, (int, float)):
        # Pass through without pre-coercion so _number_action can decide
        # whether to preserve fractional values (e.g. 22.5 for climate).
        return _number_action(value, domain, entity_id)
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


def _number_action(n: float | int, domain: str, entity_id: str) -> dict | None:
    # Climate is the only domain where fractional values are preserved
    # (e.g. 22.5 °C). Other numeric domains use integer units in HA.
    if domain == "climate":
        return {
            "service": "climate.set_temperature",
            "target": {"entity_id": entity_id},
            "data": {"temperature": n},
        }
    if domain == "light":
        return {
            "service": "light.turn_on",
            "target": {"entity_id": entity_id},
            "data": {"brightness_pct": int(n)},
        }
    if domain == "fan":
        return {
            "service": "fan.set_percentage",
            "target": {"entity_id": entity_id},
            "data": {"percentage": int(n)},
        }
    if domain == "cover":
        return {
            "service": "cover.set_cover_position",
            "target": {"entity_id": entity_id},
            "data": {"position": int(n)},
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
