"""
opalib.physics - all of the major fields of physics calculations.
"""

import math
from typing import Optional, Union, List

# SCIENTIFIC CONSTANTS
G_CONSTANT = 6.67430e-11 # Gravitational Constant (m^3 kg^-1 s^-2)
C_SPEED_LIGHT = 299792458 # Speed of Light in vacuum (m/s)
H_PLANCK = 6.62607015e-34 # Planck Constant (J*s)
K_BOLTZMANN = 1.380649e-23 # Boltzmann Constant (J/K)
E_CHARGE = 1.60217663e-19 # Elementary Charge (Coulombs)
EPSILON_0 = 8.85418781e-12 # Vacuum Permittivity (F/m)
K_COULOMB = 8.98755179e9 # Coulomb Constant (N*m^2/C^2)
G_EARTH = 9.80665 # Standard Earth gravity (m/s^2)
R_UNIVERSAL = 8.3144626 # Universal Gas Constant (J/mol*K)

# KINEMATICS & PROJECTILE MOTION (w/ CUSTOM GRAVITY)
def kinematic_v(u: float, a: float, t: float) -> float:
    """Solves v = u + at (Final Velocity)"""
    return u + (a * t)

def kinematic_s(u: float, t: float, a: float) -> float:
    """Solves s = ut + 0.5at^2 (Displacement)"""
    return (u * t) + (0.5 * a * (t ** 2))

def kinematic_v2(u: float, a: float, s: float) -> float:
    """Solves v^2 = u^2 + 2as. Returns final velocity v (handles negatives safely)."""
    val = (u ** 2) + (2 * a * s)
    return math.sqrt(val) if val >= 0 else 0.0

def kinematic_s_no_a(u: float, v: float, t: float) -> float:
    """Solves s = 0.5 * (u + v) * t"""
    return 0.5 * (u + v) * t

def time_of_flight(v0: float, theta_deg: float, g: float = G_EARTH) -> float:
    """Solves t = (2 * v0 * sin(theta)) / g. Returns inf if gravity is zero."""
    if g <= 0: return float('inf')
    return (2 * v0 * math.sin(math.radians(theta_deg))) / g

def horizontal_range(v0: float, theta_deg: float, g: float = G_EARTH) -> float:
    """Solves R = (v0^2 * sin(2*theta)) / g. Returns inf if gravity is zero."""
    if g <= 0: return float('inf')
    return (v0**2 * math.sin(2 * math.radians(theta_deg))) / g

def max_height(v0: float, theta_deg: float, g: float = G_EARTH) -> float:
    """Solves H = (v0^2 * sin^2(theta)) / (2g). Returns inf if gravity is zero."""
    if g <= 0: return float('inf')
    return (v0**2 * (math.sin(math.radians(theta_deg))**2)) / (2 * g)

def free_fall_time(height: float, g: float = G_EARTH) -> float:
    """Solves t = sqrt(2h / g). Airtime when dropping straight down."""
    if g <= 0 or height < 0: return float('inf')
    return math.sqrt((2 * height) / g)

# DYNAMICS, FORCE, & ENERGY
def newton_second_law(m: Optional[float] = None, a: Optional[float] = None, f: Optional[float] = None) -> float:
    """Solves F = m * a for whichever single parameter is omitted (None)."""
    if f is None and m is not None and a is not None: return m * a
    if m is None and f is not None and a is not None: return f / a if a != 0 else float('inf')
    if a is None and f is not None and m is not None: return f / m if m != 0 else float('inf')
    raise ValueError("Provide exactly two arguments.")

def kinetic_energy(m: float, v: float) -> float:
    """Solves KE = 0.5 * m * v^2"""
    return 0.5 * m * (v ** 2)

def potential_energy(m: float, h: float, g: float = G_EARTH) -> float:
    """Solves PE = m * g * h"""
    return m * g * h

def spring_potential_energy(k: float, x: float) -> float:
    """Solves PE_spring = 0.5 * k * x^2 (Hooke's Law Energy)"""
    return 0.5 * k * (x ** 2)

def hookes_law_force(k: float, x: float) -> float:
    """Solves F = -k * x (Spring Restoring Force)"""
    return -k * x

def momentum(m: float, v: float) -> float:
    """Solves p = m * v"""
    return m * v

def impulse(force: float, time_delta: float) -> float:
    """Solves J = F * delta_t"""
    return force * time_delta

def work_done(force: float, distance: float, theta_deg: float = 0.0) -> float:
    """Solves W = F * d * cos(theta)"""
    return force * distance * math.cos(math.radians(theta_deg))

def power(work: float, time: float) -> float:
    """Solves P = W / t"""
    return work / time if time != 0 else float('inf')

def friction_force(mu: float, normal_force: float) -> float:
    """Solves F_f = mu * F_N (Static/Kinetic Friction)"""
    return mu * normal_force

# ROTATIONAL MECHANICS
def angular_velocity(theta_rad: float, time: float) -> float:
    """Solves omega = delta_theta / t"""
    return theta_rad / time if time != 0 else float('inf')

def centripetal_acceleration(v_linear: float, radius: float) -> float:
    """Solves a_c = v^2 / r"""
    return (v_linear ** 2) / radius if radius != 0 else float('inf')

def centripetal_force(m: float, v_linear: float, radius: float) -> float:
    """Solves F_c = m * v^2 / r"""
    return (m * (v_linear ** 2)) / radius if radius != 0 else float('inf')

def torque(force: float, radius: float, theta_deg: float = 90.0) -> float:
    """Solves tau = r * F * sin(theta)"""
    return radius * force * math.sin(math.radians(theta_deg))

def pendulum_period(length: float, g: float = G_EARTH) -> float:
    """Solves T = 2 * pi * sqrt(L / g)"""
    if g <= 0 or length < 0: return float('inf')
    return 2 * math.pi * math.sqrt(length / g)

def mass_spring_period(m: float, k: float) -> float:
    """Solves T = 2 * pi * sqrt(m / k)"""
    if k <= 0 or m < 0: return float('inf')
    return 2 * math.pi * math.sqrt(m / k)

# GRAVITATION & ORBITAL SPACE PHYSICS
def gravitational_force(m1: float, m2: float, r: float) -> float:
    """Solves F = G * m1 * m2 / r^2"""
    return (G_CONSTANT * m1 * m2) / (r ** 2) if r != 0 else float('inf')

def calculate_surface_gravity(mass: float, radius: float) -> float:
    """Solves g = G * M / r^2"""
    return (G_CONSTANT * mass) / (radius ** 2) if radius != 0 else float('inf')

def orbital_velocity(m_central: float, r: float) -> float:
    """Solves v = sqrt(G * M / r)"""
    if r <= 0: return float('inf')
    return math.sqrt((G_CONSTANT * m_central) / r)

def escape_velocity(m_central: float, r: float) -> float:
    """Solves v_e = sqrt(2 * G * M / r)"""
    if r <= 0: return float('inf')
    return math.sqrt((2 * G_CONSTANT * m_central) / r)

# FLUID DYNAMICS & HYDROSTATICS
def fluid_pressure(density: float, depth: float, g: float = G_EARTH, p_atm: float = 101325.0) -> float:
    """Solves P = P_0 + rho * g * h"""
    return p_atm + (density * g * depth)

def buoyant_force(fluid_density: float, volume_submerged: float, g: float = G_EARTH) -> float:
    """Solves F_b = rho * V * g (Archimedes' Principle)"""
    return fluid_density * volume_submerged * g

def torricelli_velocity(h: float, g: float = G_EARTH) -> float:
    """Solves v = sqrt(2 * g * h) (Fluid draining velocity)"""
    val = 2 * g * h
    return math.sqrt(val) if val >= 0 else 0.0

# THERMODYNAMICS & GASES
def ideal_gas_law(p: Optional[float] = None, v: Optional[float] = None, 
                  n: Optional[float] = None, t: Optional[float] = None) -> float:
    """Solves PV = nRT for whichever single argument is left out (None)."""
    if p is None: return (n * R_UNIVERSAL * t) / v
    if v is None: return (n * R_UNIVERSAL * t) / p
    if n is None: return (p * v) / (R_UNIVERSAL * t)
    if t is None: return (p * v) / (n * R_UNIVERSAL)
    raise ValueError("Provide exactly three arguments.")

def heat_energy(m: float, c: float, delta_t: float) -> float:
    """Solves Q = m * c * delta_T (Specific Heat Capacity transfer)"""
    return m * c * delta_t

# ELECTRICITY & CIRCUIT PROPERTIES
def ohms_law(v: Optional[float] = None, i: Optional[float] = None, r: Optional[float] = None) -> float:
    """Solves V = I * R for whichever single parameter is omitted (None)."""
    if v is None: return i * r
    if i is None: return v / r if r != 0 else float('inf')
    if r is None: return v / i if i != 0 else float('inf')
    raise ValueError("Provide exactly two arguments.")

def electrical_power(v: float, i: float) -> float:
    """Solves P = V * I"""
    return v * i

def coulomb_law(q1: float, q2: float, r: float) -> float:
    """Solves F = k * |q1 * q2| / r^2 (Electrostatic Force)"""
    return (K_COULOMB * abs(q1 * q2)) / (r ** 2) if r != 0 else float('inf')

def series_resistance(resistors: List[float]) -> float:
    """Calculates total resistance in series: R1 + R2 + ..."""
    return sum(resistors)

def parallel_resistance(resistors: List[float]) -> float:
    """Calculates total resistance in parallel: 1 / (1/R1 + 1/R2 + ...)"""
    if 0.0 in resistors: return 0.0
    return 1.0 / sum(1.0 / r for r in resistors)

# WAVES & OPTICS
def wave_speed(frequency: float, wavelength: float) -> float:
    """Solves v = f * lambda"""
    return frequency * wavelength

def snells_law_n2(n1: float, theta1_deg: float, theta2_deg: float) -> float:
    """Solves n1 * sin(theta1) = n2 * sin(theta2) for refractive index n2."""
    sin_t2 = math.sin(math.radians(theta2_deg))
    if sin_t2 == 0: return float('inf')
    return (n1 * math.sin(math.radians(theta1_deg))) / sin_t2

# MODERN & QUANTUM PHYSICS
def mass_energy_equivalence(m: float) -> float:
    """Solves E = m * c^2"""
    return m * (C_SPEED_LIGHT ** 2)

def photon_energy(frequency: float) -> float:
    """Solves E = h * f"""
    return H_PLANCK * frequency

def de_broglie_wavelength(m: float, v: float) -> float:
    """Solves lambda = h / (m * v)"""
    p = m * v
    return H_PLANCK / p if p != 0 else float('inf')
