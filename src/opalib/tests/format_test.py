"""Tests for the format module."""

import unittest
import opalib.format as format
import opalib.util as util


class TestFormat(unittest.TestCase):
    def test_bool_save_load(self):
        data = []
        format.Bool["save"](data, True)
        result, _ = format.Bool["load"](b"".join(data), 0)
        self.assertTrue(result)

    def test_string_save_and_read(self):
        data = []
        format.String["save"](data, "hello")
        result, _ = util.read_s(b"".join(data), 0)
        self.assertEqual(result, "hello")

    def test_challenge_format_defined(self):
        self.assertTrue(hasattr(format, "Challenge"))
        self.assertTrue(isinstance(format.Challenge, dict))

    def test_challenge_round_trip(self):
        ctx = util.Context()
        value = {
            "signature": [1] * 16,
            "issued": 123456789012345678,
            "difficulty": 4,
            "K00": 1,
            "K01": 2,
            "K10": 3,
            "K11": 4,
        }

        data = []
        util.save(data, value, format.Challenge, ctx)
        raw = b"".join(data)

        result, _ = util.load(raw, 0, format.Challenge, util.Context())
        self.assertEqual(result, value)

    def test_F_alias_reflects_module_globals(self):
        self.assertTrue(hasattr(format, "F"))
        self.assertIs(format.F.Challenge, format.Challenge)
