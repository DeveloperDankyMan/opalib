"""Unit tests for opalib.physics."""

import unittest
from src import (
    force,
    kinetic_energy,
    potential_energy,
    fall_time,
    projectile_range,
    projectile_max_height,
    projectile_time_of_flight,
    GRAVITY_EARTH,
)


class TestPhysics(unittest.TestCase):
    def test_force(self):
        self.assertEqual(force(10, 9.8), 98.0)

    def test_kinetic_energy(self):
        self.assertEqual(kinetic_energy(2, 3), 9.0)

    def test_potential_energy(self):
        self.assertEqual(potential_energy(1, 2, gravity=10), 20)

    def test_fall_time(self):
        self.assertAlmostEqual(fall_time(4, gravity=GRAVITY_EARTH), 0.9032015115035751, places=6)

    def test_projectile_range(self):
        result = projectile_range(10, 45, gravity=GRAVITY_EARTH)
        self.assertAlmostEqual(result, (10 * 10 * 1.0) / GRAVITY_EARTH, places=4)

    def test_projectile_max_height(self):
        result = projectile_max_height(10, 45, gravity=GRAVITY_EARTH)
        self.assertAlmostEqual(result, (10 * 10 * 0.5) / (2 * GRAVITY_EARTH), places=4)

    def test_projectile_time_of_flight(self):
        result = projectile_time_of_flight(10, 45, gravity=GRAVITY_EARTH)
        self.assertAlmostEqual(result, (2 * 10 * 0.70710678) / GRAVITY_EARTH, places=4)

    def test_fall_time_negative_height(self):
        with self.assertRaises(ValueError):
            fall_time(-1)
