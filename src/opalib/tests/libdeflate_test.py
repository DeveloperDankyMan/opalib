"""Tests for the libdeflate module."""

import unittest
from opalib import LibDeflate


class TestLibDeflate(unittest.TestCase):
    def test_deflate_roundtrip(self):
        payload = b"hello world\x00\x00"
        compressed = LibDeflate.CompressDeflate(payload, {"level": 9})
        decompressed = LibDeflate.DecompressDeflate(compressed)

        self.assertEqual(decompressed, payload)

    def test_zlib_roundtrip(self):
        payload = b"hello zlib"
        compressed = LibDeflate.CompressZlib(payload)
        decompressed = LibDeflate.DecompressZlib(compressed)
        self.assertEqual(decompressed, payload)
