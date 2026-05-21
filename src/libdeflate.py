"""libdeflate - minimal DEFLATE wrappers for opalib."""

import zlib
from typing import Any, Dict, Optional, Union


def _to_bytes(value: Union[str, bytes]) -> bytes:
    if isinstance(value, str):
        return value.encode("latin1")
    return value


class LibDeflateClass:
    """Minimal wrapper around Python's zlib for raw DEFLATE data."""

    def CompressDeflate(
        self,
        data: Union[str, bytes],
        configs: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Compress raw data using DEFLATE with no zlib header."""
        bytes_data = _to_bytes(data)
        level = 9
        if configs is not None and isinstance(configs, dict):
            if "level" in configs:
                level = int(configs["level"])

        compressor = zlib.compressobj(level, zlib.DEFLATED, -zlib.MAX_WBITS)
        return compressor.compress(bytes_data) + compressor.flush()

    def DecompressDeflate(self, data: Union[str, bytes]) -> bytes:
        """Decompress raw DEFLATE bytes."""
        bytes_data = _to_bytes(data)
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
        return decompressor.decompress(bytes_data) + decompressor.flush()

    def CompressZlib(
        self,
        data: Union[str, bytes],
        configs: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Compress data using zlib wrapper format."""
        bytes_data = _to_bytes(data)
        level = 9
        if configs is not None and isinstance(configs, dict):
            if "level" in configs:
                level = int(configs["level"])

        return zlib.compress(bytes_data, level)

    def DecompressZlib(self, data: Union[str, bytes]) -> bytes:
        """Decompress zlib-wrapped compressed data."""
        bytes_data = _to_bytes(data)
        return zlib.decompress(bytes_data)


LibDeflate = LibDeflateClass()

__all__ = ["LibDeflate"]
