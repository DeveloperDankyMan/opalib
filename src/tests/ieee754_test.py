"""Tests for the ieee754 module."""

import unittest
from src import ieee754


class TestIEEE754(unittest.TestCase):
    def test_double_roundtrip(self):
        value = 3.141592653589793
        binary = ieee754.double2bin(value)
        self.assertEqual(ieee754.bin2double(binary), value)

    def test_bin2double_requires_eight_bytes(self):
        with self.assertRaises(ValueError):
            ieee754.bin2double(b"123")
