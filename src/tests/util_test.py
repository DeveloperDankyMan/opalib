"""Tests for the util module."""

import unittest
from src import util


class TestUtil(unittest.TestCase):
    def test_mod1(self):
        self.assertEqual(util.mod1_dec(1, 5), 5)
        self.assertEqual(util.mod1_inc(4, 5), 5)

    def test_validate_bool(self):
        self.assertTrue(util.validate_bool("t"))
        self.assertFalse(util.validate_bool("false"))
        self.assertIsNone(util.validate_bool("maybe"))

    def test_b2i_and_b2i64(self):
        self.assertEqual(util.b2i(b"\x01\x00\x00\x00"), 1)
        self.assertEqual(util.b2i64(b"\x01\x00\x00\x00\x00\x00\x00\x00"), 1)

    def test_vector_roundtrip(self):
        vec = util.Vector3(1.0, 2.0, 3.0)
        data = util.v2b(vec)
        result, _ = util.read_v(data, 0)
        self.assertEqual(result, vec)

    def test_encode_decode_zeros(self):
        payload = b"\x00\x00ABC\xff"
        encoded = util.encode_zeros(payload)
        decoded = util.decode_zeros(encoded)
        self.assertEqual(decoded, payload)

    def test_encode_decode_with_deflate(self):
        payload = b"test payload\x00\x00"
        encoded = util.encode(payload)
        decoded = util.decode(encoded)
        self.assertEqual(decoded, payload)
