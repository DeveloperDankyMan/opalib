"""opalib.units - unit conversion helpers for length and custom measures."""

from typing import Dict, Iterable, Optional, Sequence, Tuple

STUD_TO_METER = 0.28
"""Conversion factor from studs to meters."""

_UNIT_FACTORS: Dict[str, float] = {}

_DEFAULT_UNIT_DEFINITIONS: Dict[str, Tuple[float, Tuple[str, ...]]] = {
    "meter": (1.0, ("meters", "m")),
    "stud": (STUD_TO_METER, ("studs", "st")),
    "foot": (0.3048, ("feet", "ft")),
    "inch": (0.0254, ("inches", "in")),
    "kilometer": (1000.0, ("kilometers", "km")),
}


def _register_default_units() -> None:
    for name, (factor, aliases) in _DEFAULT_UNIT_DEFINITIONS.items():
        _UNIT_FACTORS[name] = factor
        for alias in aliases:
            _UNIT_FACTORS[alias] = factor

_register_default_units()

__all__ = [
    "STUD_TO_METER",
    "to_meters",
    "from_meters",
    "convert",
    "register_unit",
    "list_units",
    "supported_units",
]


def _normalize_unit(unit: str) -> str:
    return unit.strip().lower()


def _get_factor(unit: str) -> float:
    unit_key = _normalize_unit(unit)
    if unit_key not in _UNIT_FACTORS:
        supported = ", ".join(sorted(supported_units()))
        raise ValueError(
            f"Unsupported unit: {unit!r}. Supported units: {supported}"
        )
    return _UNIT_FACTORS[unit_key]


def to_meters(value: float, unit: str) -> float:
    """Convert a value from a supported unit to meters."""
    return value * _get_factor(unit)


def from_meters(value: float, unit: str) -> float:
    """Convert a value in meters to a supported unit."""
    return value / _get_factor(unit)


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a value between two supported units."""
    meters = to_meters(value, from_unit)
    return from_meters(meters, to_unit)


def register_unit(name: str, factor_to_meters: float, aliases: Optional[Sequence[str]] = None) -> None:
    """Register a custom unit conversion factor to meters.

    Args:
        name: Canonical unit name.
        factor_to_meters: Conversion factor from the unit to meters.
        aliases: Optional alternate spellings for the same unit.
    """
    if factor_to_meters <= 0:
        raise ValueError("Conversion factor must be positive")

    unit_key = _normalize_unit(name)
    _UNIT_FACTORS[unit_key] = factor_to_meters
    if aliases:
        for alias in aliases:
            _UNIT_FACTORS[_normalize_unit(alias)] = factor_to_meters


def supported_units() -> Iterable[str]:
    """Return all supported unit names and aliases."""
    return sorted(_UNIT_FACTORS)


def list_units() -> Dict[str, float]:
    """Return all registered unit conversion factors."""
    return {unit: _UNIT_FACTORS[unit] for unit in supported_units()}
