"""ieee754 - IEEE 754 double conversion helpers."""

import struct
from typing import Union


def _to_bytes(value: Union[str, bytes]) -> bytes:
    if isinstance(value, str):
        return value.encode("latin1")
    return value


def bin2double(value: Union[str, bytes]) -> float:
    """Convert an 8-byte sequence to a double-precision float."""
    raw = _to_bytes(value)
    if len(raw) != 8:
        raise ValueError("bin2double requires exactly 8 bytes")
    return struct.unpack("<d", raw)[0]


def double2bin(value: float) -> bytes:
    """Convert a double-precision float to an 8-byte sequence."""
    return struct.pack("<d", value)

__all__ = ["bin2double", "double2bin"]
