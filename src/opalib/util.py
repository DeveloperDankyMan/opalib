"""util - low-level binary and utility helpers converted from util.lua."""

from __future__ import annotations

import math
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from . import ieee754, libdeflate as LibDeflate

@dataclass
class Vector3:
    X: float
    Y: float
    Z: float


prec = 1e-3
prec2 = prec ** 2

_epsilon = 1.0
while 1.0 + _epsilon != 1.0:
    _epsilon *= 0.5

e = _epsilon

max_parallel_angle = 1
mpa_cos = math.cos(max_parallel_angle / 360 * 2 * math.pi)


class Context:
    def __init__(self) -> None:
        self.stack: List[Any] = []
        self._attrs: Dict[str, Any] = {}

    def __getitem__(self, key: Union[int, str]) -> Any:
        if isinstance(key, int):
            return self.stack[key - 1]
        return self._attrs[key]

    def __setitem__(self, key: Union[int, str], value: Any) -> None:
        if isinstance(key, int):
            index = key - 1
            if index == len(self.stack):
                self.stack.append(value)
            elif 0 <= index < len(self.stack):
                self.stack[index] = value
            else:
                raise IndexError("Context index out of range")
        else:
            self._attrs[key] = value

    def __getattr__(self, name: str) -> Any:
        if name in {"stack", "_attrs"}:
            raise AttributeError
        return self._attrs.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"stack", "_attrs"}:
            super().__setattr__(name, value)
        else:
            self._attrs[name] = value

    def __len__(self) -> int:
        return len(self.stack)


def _to_bytes(value: Union[str, bytes, bytearray, List[bytes], Tuple[bytes, ...]]) -> bytes:
    if isinstance(value, str):
        return value.encode("latin1")
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, list) or isinstance(value, tuple):
        return b"".join(value)
    return value


def mod1_dec(x: float, m: float) -> float:
    return (x - 2) % m + 1


def mod1_inc(x: float, m: float) -> float:
    return x % m + 1


def bind(f: Callable[..., Any], obj: Any) -> Callable[..., Any]:
    def bound(*args: Any, **kwargs: Any) -> Any:
        return f(obj, *args, **kwargs)

    return bound


def union_k(*dicts: Dict[Any, Any]) -> Dict[Any, Any]:
    result: Dict[Any, Any] = {}
    for source in dicts:
        result.update(source)
    return result


def union_i(*iterables: List[Any]) -> List[Any]:
    result: List[Any] = []
    for sequence in iterables:
        result.extend(sequence)
    return result


def validate_bool(txt: str) -> Optional[bool]:
    lower = txt.lower()
    if lower in {"true", "t"}:
        return True
    if lower in {"false", "f"}:
        return False
    return None


def get_trace(msg: str) -> str:
    return f"{msg}; {traceback.format_exc()}"


def pcall(f: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[bool, Any]:
    try:
        return True, f(*args, **kwargs)
    except Exception as exc:
        return False, get_trace(str(exc))


b2d = ieee754.bin2double

d2b = ieee754.double2bin


def b2i(b: Union[str, bytes]) -> int:
    raw = _to_bytes(b)
    return int.from_bytes(raw, byteorder="little", signed=False)


def b2i64(b: Union[str, bytes]) -> int:
    raw = _to_bytes(b)
    return int.from_bytes(raw, byteorder="little", signed=False)


def b2v(b: Union[str, bytes]) -> Vector3:
    raw = _to_bytes(b)
    x = b2d(raw[0:8])
    y = b2d(raw[8:16])
    z = b2d(raw[16:24])
    return Vector3(X=x, Y=y, Z=z)


def read_i(data: Union[str, bytes], i: int) -> Tuple[int, int]:
    raw = _to_bytes(data)
    value = int.from_bytes(raw[i : i + 4], byteorder="little", signed=False)
    return value, i + 4


def read_i64(data: Union[str, bytes], i: int) -> Tuple[int, int]:
    raw = _to_bytes(data)
    value = int.from_bytes(raw[i : i + 8], byteorder="little", signed=False)
    return value, i + 8


def read_d(data: Union[str, bytes], i: int) -> Tuple[float, int]:
    raw = _to_bytes(data)
    value = b2d(raw[i : i + 8])
    return value, i + 8


def read_v(data: Union[str, bytes], i: int) -> Tuple[Vector3, int]:
    raw = _to_bytes(data)
    vector = b2v(raw[i : i + 24])
    return vector, i + 24


def read_t(data: Union[str, bytes], i: int) -> Tuple[int, int]:
    raw = _to_bytes(data)
    return raw[i], i + 1


def read_s(data: Union[str, bytes], i: int) -> Tuple[str, int]:
    raw = _to_bytes(data)
    length, i = read_i(raw, i)
    value = raw[i : i + length].decode("latin1")
    return value, i + length


def read_a(data: Union[str, bytes], i: int) -> Tuple[Any, int]:
    raw = _to_bytes(data)
    ty, i = read_t(raw, i)
    if ty == 0:
        return read_s(raw, i)
    if ty == 1:
        return read_d(raw, i)
    raise ValueError(f"Received unknown field type: {ty}")


def decode(value: Union[str, bytes]) -> bytes:
    return LibDeflate.decompress_deflate(decode_zeros(_to_bytes(value))) # LibDeflate.DecompressDeflate(decode_zeros(_to_bytes(value)))


def decode_params(data: Union[str, bytes], i: int) -> Tuple[Dict[str, Any], int]:
    raw = _to_bytes(data)
    fields: Dict[str, Any] = {}
    n, i = read_i(raw, i)
    for _ in range(n):
        name, i = read_s(raw, i)
        value, i = read_a(raw, i)
        fields[name] = value
    return fields, i


def load(
    data: Union[str, bytes],
    i: int,
    format: Optional[Dict[str, Any]],
    context: Context,
) -> Tuple[Any, int]:
    raw = _to_bytes(data)
    if format is None:
        return None, i

    class_format = None
    if isinstance(format, dict) and "format" in format:
        class_format = format
        format = format["format"]

    obj: Any = None
    if isinstance(format, dict) and not format:
        # format.ID is represented by an empty dictionary in this conversion.
        obj = len(context) + 1
    elif isinstance(format, dict) and "type" in format:
        fmt_type = format["type"]
        if fmt_type == "compat":
            obj, i = load(raw, i, format["func"](context), context)
        elif fmt_type == "ref":
            id_ = None
            id_, i = read_i(raw, i)
            obj = context[format["of"]][id_]
        elif fmt_type == "konst":
            if format.get("is_serialized"):
                obj, i = load(raw, i, format["v_format"], context)
            else:
                obj = format["value"]
        elif fmt_type == "save":
            obj, i = load(raw, i, format["v_format"], context)
            context[format["name"]] = obj
        elif fmt_type == "enable_if":
            if format["cond"](raw, i, context):
                obj, i = load(raw, i, format["v_format"], context)
        elif fmt_type == "union":
            obj = {}
            for v_format in format["formats"]:
                context.obj = obj
                obj, i = load(raw, i, v_format, context)
        else:
            obj = getattr(context, "obj", None)
            if obj is not None:
                context.obj = None
            else:
                obj = {}

            if format.get("key"):
                context[format["key"]] = obj

            if fmt_type == "struct":
                for field in format["fields"]:
                    for k, v_format in field.items():
                        obj[k], i = load(raw, i, v_format, context)
            elif fmt_type == "array":
                v_format = format["v_format"]
                arr: List[Any] = []
                for _ in range(format["len"]):
                    item, i = load(raw, i, v_format, context)
                    arr.append(item)
                obj = arr
            else:
                n, i = read_i(raw, i)
                stack_id = len(context) + 1
                context[stack_id] = obj
                if fmt_type == "list":
                    v_format = format["v_format"]
                    arr = []
                    for _ in range(n):
                        item, i = load(raw, i, v_format, context)
                        arr.append(item)
                    obj = arr
                elif fmt_type == "map":
                    v_format_k = format["k_format"]
                    v_format_v = format["v_format"]
                    for _ in range(n):
                        key, i = load(raw, i, v_format_k, context)
                        if key is not None:
                            value, i = load(raw, i, v_format_v, context)
                            obj[key] = value
                context[stack_id] = None

    if class_format is not None and isinstance(class_format, dict) and class_format.get("MT"):
        # Python does not support Lua metatables directly. Skip this behavior.
        pass

    if isinstance(format, dict) and format.get("load"):
        obj, i = format["load"](raw, i)

    return obj, i


def a(data: List[bytes], value: bytes) -> None:
    data.append(value)
    if hasattr(data, "size"):
        data.size += len(value)


def i2b(x: int) -> bytes:
    return x.to_bytes(4, byteorder="little", signed=False)


def i642b(x: int) -> bytes:
    return x.to_bytes(8, byteorder="little", signed=False)


def v2b(v: Vector3) -> bytes:
    return d2b(v.X) + d2b(v.Y) + d2b(v.Z)


def s2b(s: str) -> bytes:
    encoded = s.encode("latin1")
    return i2b(len(encoded)) + encoded


def a2b(v: Any) -> bytes:
    if isinstance(v, str):
        return b"\x00" + s2b(v)
    if isinstance(v, (int, float)):
        return b"\x01" + d2b(float(v))
    raise TypeError("Unsupported value type for a2b")


def encode(value: Union[str, bytes]) -> bytes:
    return encode_zeros(LibDeflate.compress_deflate(_to_bytes(value), {"level": 9}))

special = bytes([255])
null = bytes([0])


def encode_zeros(value: Union[str, bytes]) -> bytes:
    raw = _to_bytes(value)
    result: List[bytes] = []
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if b == 0:
            m = 1
            while i + 1 < n and m < 254 and raw[i + 1] == 0:
                m += 1
                i += 1
            result.append(special)
            result.append(bytes([m]))
        elif b == 255:
            result.append(special)
            result.append(special)
        else:
            result.append(bytes([b]))
        i += 1
    return b"".join(result)


def decode_zeros(value: Union[str, bytes]) -> bytes:
    raw = _to_bytes(value)
    result: List[bytes] = []
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if b == 255:
            i += 1
            b2 = raw[i]
            if b2 == 255:
                result.append(special)
            else:
                result.extend([null] * b2)
        else:
            result.append(bytes([b]))
        i += 1
    return b"".join(result)


def save(data: List[bytes], obj: Any, format: Optional[Dict[str, Any]], context: Context) -> None:
    if not format:
        return

    if isinstance(format, dict) and "format" in format:
        format = format["format"]

    if isinstance(format, dict) and "type" in format:
        fmt_type = format["type"]
        if fmt_type == "compat":
            save(data, obj, format["func"](context), context)
        elif fmt_type == "ref":
            a(data, i2b(obj.id))
        elif fmt_type == "konst":
            if format.get("is_serialized"):
                save(data, format["value"], format["v_format"], context)
        elif fmt_type == "save":
            save(data, obj, format["v_format"], context)
            if format["v_format"].get("type") == "konst":
                context[format["name"]] = format["v_format"]["value"]
            else:
                context[format["name"]] = obj
        elif fmt_type == "enable_if":
            save(data, obj, format["v_format"], context)
        elif fmt_type == "union":
            for v_format in format["formats"]:
                save(data, obj, v_format, context)
        elif fmt_type == "struct":
            for field in format["fields"]:
                for _, v_format in field.items():
                    save(data, obj.get(next(iter(field.keys())), None), v_format, context)
        elif fmt_type == "array":
            for value in obj:
                save(data, value, format["v_format"], context)
        elif fmt_type == "list":
            a(data, i2b(len(obj)))
            for value in obj:
                save(data, value, format["v_format"], context)
        elif fmt_type == "map":
            a(data, i2b(len(obj)))
            for key, value in obj.items():
                save(data, key, format["k_format"], context)
                save(data, value, format["v_format"], context)
        else:
            raise ValueError(f"Unknown format type: {fmt_type}")

    if isinstance(format, dict) and format.get("save"):
        format["save"](data, obj)


__all__ = [
    "Vector3",
    "Context",
    "mod1_dec",
    "mod1_inc",
    "bind",
    "union_k",
    "union_i",
    "validate_bool",
    "get_trace",
    "pcall",
    "b2d",
    "b2i",
    "b2i64",
    "b2v",
    "read_i",
    "read_i64",
    "read_d",
    "read_v",
    "read_t",
    "read_s",
    "read_a",
    "decode",
    "decode_params",
    "load",
    "a",
    "i2b",
    "i642b",
    "v2b",
    "s2b",
    "a2b",
    "encode",
    "encode_zeros",
    "decode_zeros",
    "save",
]
