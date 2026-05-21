"""Format definitions converted from format.lua to Python.

This module exposes binary format descriptors directly at module scope.
Example usage:
    import src.format as format
    format.Bool["save"](data, True)
    format.Challenge
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Dict, List, Optional

from . import util

_VERSION = 3

class _RefProxy:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def __getattr__(self, name: str) -> Dict[str, Any]:
        if name not in self._cache:
            self._cache[name] = {"type": "ref", "of": name}
        return self._cache[name]

    def __dir__(self) -> List[str]:
        return sorted(name for name in globals().keys() if not name.startswith("_"))


Ref = _RefProxy()


def map(k_format: Any, v_format: Any) -> Dict[str, Any]:
    return {"type": "map", "k_format": k_format, "v_format": v_format}


def list(v_format: Any, key: Optional[str] = None) -> Dict[str, Any]:
    return {"type": "list", "v_format": v_format, "key": key}


def array(length: int, v_format: Any, key: Optional[str] = None) -> Dict[str, Any]:
    return {"type": "array", "len": length, "v_format": v_format, "key": key}


def union(*formats: Any) -> Dict[str, Any]:
    return {"type": "union", "formats": list(formats)}


def struct(fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"type": "struct", "fields": fields}


def konst(value: Any, v_format: Any, is_serialized: bool = False) -> Dict[str, Any]:
    return {
        "type": "konst",
        "value": value,
        "v_format": v_format,
        "is_serialized": is_serialized,
    }


def save(name: str, v_format: Any) -> Dict[str, Any]:
    return {"type": "save", "name": name, "v_format": v_format}


def compat(func: Callable[[Any], Any]) -> Dict[str, Any]:
    return {"type": "compat", "func": func}


def enable_if(cond: Callable[[bytes, int, util.Context], bool], v_format: Any) -> Dict[str, Any]:
    return {"type": "enable_if", "cond": cond, "v_format": v_format}


def format(name: str, t: Dict[str, Any]) -> None:
    t["name"] = name
    setattr(sys.modules[__name__], name, t)


def new(name: str, t: Dict[str, Any]) -> Dict[str, Any]:
    t["name"] = name
    setattr(sys.modules[__name__], name, t)
    return t


def GE_VER(ver: int, on_true: Any, on_false: Any) -> Dict[str, Any]:
    return compat(lambda ctx: on_true if getattr(ctx, "version", 0) >= ver else on_false)


String: Dict[str, Any] = {
    "load": util.read_s,
    "save": lambda data, value: util.a(data, util.s2b(value)),
}

Bool: Dict[str, Any] = {
    "load": lambda raw, i: (raw[i : i + 1] == b"\x01", i + 1),
    "save": lambda data, value: util.a(data, b"\x01" if value else b"\x00"),
}

V3: Dict[str, Any] = {
    "load": util.read_v,
    "save": lambda data, value: util.a(data, util.v2b(value)),
}

Byte: Dict[str, Any] = {
    "load": lambda raw, i: (raw[i], i + 1),
    "save": lambda data, value: util.a(data, bytes([value])),
}

Double: Dict[str, Any] = {
    "load": util.read_d,
    "save": lambda data, value: util.a(data, util.d2b(value)),
}

Int: Dict[str, Any] = {
    "load": util.read_i,
    "save": lambda data, value: util.a(data, util.i2b(value)),
}

Int64: Dict[str, Any] = {
    "load": util.read_i64,
    "save": lambda data, value: util.a(data, util.i642b(value)),
}

Any: Dict[str, Any] = {
    "load": util.read_a,
    "save": lambda data, value: util.a(data, util.a2b(value)),
}

ID: Dict[str, Any] = {}


new(
    "Challenge",
    struct(
        [
            {"signature": array(16, Byte)},
            {"issued": Int64},
            {"difficulty": Byte},
            {"K00": Int},
            {"K01": Int},
            {"K10": Int},
            {"K11": Int},
        ]
    ),
)


new(
    "Solution",
    struct(
        [
            {"x": Int},
            {"y": Int},
        ]
    ),
)


class _FormatAlias:
    def __getattr__(self, name: str) -> Any:
        if name in globals():
            return globals()[name]
        raise AttributeError(f"module has no attribute {name}")

    def __dir__(self) -> List[str]:
        return [name for name in globals() if not name.startswith("_")]


F = _FormatAlias()

__all__ = [
    "F",
    "Ref",
    "ID",
    "V3",
    "Byte",
    "Double",
    "Int",
    "Int64",
    "String",
    "Any",
    "Bool",
    "map",
    "list",
    "array",
    "union",
    "struct",
    "konst",
    "save",
    "compat",
    "enable_if",
    "format",
    "new",
    "GE_VER",
    "Challenge",
    "Solution",
]
