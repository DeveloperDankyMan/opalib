"""libdeflate - minimal DEFLATE wrappers for opalib."""

import zlib
from typing import Any, Dict, Optional, Union

def _to_bytes(value: Union[str, bytes]) -> bytes:
    if isinstance(value, str):
        return value.encode('latin1')
    return value

def compress_deflate(
    data: Union[str, bytes], 
    configs: Optional[Dict[str, Any]] = None
) -> bytes:
    """Compress raw data using DEFLATE with no zlib header."""
    bytes_data = _to_bytes(data)
    level = configs.get("level", 9) if configs else 9
    
    compressor = zlib.compressobj(level, zlib.DEFLATED, -zlib.MAX_WBITS)
    return compressor.compress(bytes_data) + compressor.flush()

def decompress_deflate(data: Union[str, bytes]) -> bytes:
    """Decompress raw DEFLATE bytes."""
    bytes_data = _to_bytes(data)
    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    return decompressor.decompress(bytes_data) + decompressor.flush()

def compress_zlib(
    data: Union[str, bytes], 
    configs: Optional[Dict[str, Any]] = None
) -> bytes:
    """Compress data using zlib wrapper format."""
    bytes_data = _to_bytes(data)
    level = configs.get("level", 9) if configs else 9
    return zlib.compress(bytes_data, level)

def decompress_zlib(data: Union[str, bytes]) -> bytes:
    """Decompress zlib-wrapped compressed data."""
    bytes_data = _to_bytes(data)
    return zlib.decompress(bytes_data)

__all__ = [
    "compress_deflate",
    "decompress_deflate",
    "compress_zlib",
    "decompress_zlib",
]
