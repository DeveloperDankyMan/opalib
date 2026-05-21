"""opalib.physics - simple physics helpers for motion and gravity calculations."""

from math import radians, sin, sqrt
from typing import Dict

GRAVITY_EARTH = 9.80665
GRAVITY_MOON = 1.62
GRAVITY_MARS = 3.71

__all__ = [
    "GRAVITY_EARTH",
    "GRAVITY_MOON",
    "GRAVITY_MARS",
    "force",
    "kinetic_energy",
    "potential_energy",
    "fall_time",
    "projectile_max_height",
    "projectile_range",
    "projectile_time_of_flight",
]


def force(mass: float, acceleration: float) -> float:
    """Calculate force from mass and acceleration (F = m * a)."""
    return mass * acceleration


def kinetic_energy(mass: float, velocity: float) -> float:
    """Calculate kinetic energy in joules (1/2 m v^2)."""
    return 0.5 * mass * velocity * velocity


def potential_energy(mass: float, height: float, gravity: float = GRAVITY_EARTH) -> float:
    """Calculate gravitational potential energy in joules (m * g * h)."""
    return mass * gravity * height


def fall_time(height: float, gravity: float = GRAVITY_EARTH) -> float:
    """Estimate free-fall time from a height using t = sqrt(2h/g)."""
    if height < 0:
        raise ValueError("Height must be non-negative")
    return sqrt(2 * height / gravity)


def projectile_range(velocity: float, angle_deg: float, gravity: float = GRAVITY_EARTH) -> float:
    """Compute the horizontal range of a projectile launched at an angle."""
    angle_rad = radians(angle_deg)
    return (velocity * velocity * sin(2 * angle_rad)) / gravity


def projectile_max_height(velocity: float, angle_deg: float, gravity: float = GRAVITY_EARTH) -> float:
    """Compute the maximum height reached by a projectile."""
    angle_rad = radians(angle_deg)
    return (velocity * velocity * sin(angle_rad) ** 2) / (2 * gravity)


def projectile_time_of_flight(velocity: float, angle_deg: float, gravity: float = GRAVITY_EARTH) -> float:
    """Compute the total flight time for a projectile."""
    angle_rad = radians(angle_deg)
    return (2 * velocity * sin(angle_rad)) / gravity


def jump_max_height(jump_power: float, gravity: float = GRAVITY_EARTH) -> float:
    """Estimate maximum vertical height achievable from an initial vertical velocity.

    Uses h = v^2 / (2*g). `jump_power` is treated as initial vertical velocity.
    """
    try:
        return (jump_power * jump_power) / (2 * gravity)
    except Exception:
        return 0.0
