"""Unit tests for opalib.units."""

import unittest
from opalib import convert, STUD_TO_METER, list_units, register_unit, supported_units


class TestUnits(unittest.TestCase):
    def test_convert_studs_to_meters(self):
        self.assertAlmostEqual(convert(1, "studs", "meters"), STUD_TO_METER)

    def test_convert_meters_to_studs(self):
        self.assertAlmostEqual(convert(0.28, "meters", "studs"), 1.0, places=6)

    def test_convert_feet_to_studs(self):
        self.assertAlmostEqual(convert(1, "feet", "studs"), 0.3048 / STUD_TO_METER, places=6)

    def test_register_custom_unit(self):
        register_unit("test-unit", 2.5)
        self.assertAlmostEqual(convert(2, "test-unit", "meters"), 5.0)
        self.assertIn("test-unit", list_units())

    def test_register_custom_unit_aliases(self):
        register_unit("widget", 0.5, aliases=("wdg", "widgets"))
        self.assertAlmostEqual(convert(2, "wdg", "meters"), 1.0)
        self.assertAlmostEqual(convert(2, "widgets", "meters"), 1.0)

    def test_supported_units_contains_known_unit(self):
        self.assertIn("meters", supported_units())
        self.assertIn("ft", supported_units())

    def test_unsupported_unit(self):
        with self.assertRaises(ValueError):
            convert(1, "unknown", "meters")
