"""
WAVEBREAKER VEHICLE AGENT
-------------------------
Gère la physique et applique le facteur de consommation reçu.
"""

import random
import math
from typing import Optional
from config import C

# Type hints
Meters = float
MetersPerSecond = float
Seconds = float
Kilograms = float
Liters = float

class Vehicle:
    __slots__ = (
        'id', 'x', 'v', 'a', 'lane',
        'desired_speed', 'target_speed', 'is_connected',
        'params_T', 'params_a', 'params_b',
        'co2_total', 'co2_instant',
        'fuel_total', 'fuel_instant',
        'distance_traveled', 'entry_time'
    )

    def __init__(self, uid: int, x: Meters, v: MetersPerSecond, desired_speed: MetersPerSecond, is_connected: bool = False):
        self.id = uid
        self.x = x
        self.v = v
        self.a = 0.0
        self.lane = 0
        
        # Variabilité humaine
        variability = random.uniform(0.90, 1.10) if not is_connected else 1.0
        
        self.params_T = C.physics.time_headway * variability
        self.params_a = C.physics.max_accel * (1.0 / variability)
        self.params_b = C.physics.comfort_decel * variability
        
        self.desired_speed = desired_speed * variability
        self.target_speed = self.desired_speed 
        self.is_connected = is_connected
        
        self.co2_total: Kilograms = 0.0
        self.co2_instant: Kilograms = 0.0
        self.fuel_total: Liters = 0.0
        self.fuel_instant: Liters = 0.0
        
        self.distance_traveled = 0.0
        self.entry_time = 0.0 

    def update_dynamics(self, dt: Seconds, leader: Optional['Vehicle'], emission_factor: float = 1.0) -> None:
        """
        Mise à jour physique + Calcul consommation avec Facteur.
        """
        # --- 1. IDM (Accélération) ---
        v_ratio = self.v / self.target_speed if self.target_speed > 0.1 else 1000.0
        acc_free = self.params_a * (1.0 - math.pow(v_ratio, C.physics.accel_exponent))

        acc_interaction = 0.0
        if leader is not None:
            d_net = leader.x - self.x - C.vehicle.length
            dv = self.v - leader.v 
            s_star = (C.physics.min_spacing + 
                      (self.v * self.params_T) + 
                      ((self.v * dv) / (2.0 * math.sqrt(self.params_a * self.params_b))))
            d_safe = max(d_net, 0.1)
            acc_interaction = -self.params_a * math.pow(s_star / d_safe, 2)

        self.a = acc_free + acc_interaction
        
        # --- 2. Mouvement ---
        self.v += self.a * dt
        if self.v < 0:
            self.v = 0.0
            self.a = 0.0

        step_dist = (self.v * dt) + (0.5 * self.a * dt * dt)
        self.x += step_dist
        self.distance_traveled += step_dist

        # --- 3. Consommation (Avec Facteur) ---
        self._compute_emissions(dt, emission_factor)

    def _compute_emissions(self, dt: Seconds, factor: float):
        """
        Calcule la conso instantanée et applique le facteur multiplicatif (ex: 1.3).
        """
        power_demand = max(0.0, self.a * self.v)
        
        # On applique le boost spécifiquement sur le terme lié à l'accélération
        accel_cost = C.physics.co2_accel_factor * power_demand * C.physics.accel_boost_factor
        
        base_rate = C.physics.co2_idle_emission
        base_rate += C.physics.co2_speed_factor * self.v
        base_rate += accel_cost # L'accélération coûte maintenant "boost" fois plus cher
        
        final_rate = base_rate * factor
        
        co2_step = max(0.0, final_rate * dt)
        
        self.co2_instant = co2_step / 1000.0
        self.co2_total += self.co2_instant

        self.fuel_instant = self.co2_instant * C.physics.fuel_conversion_factor
        self.fuel_total += self.fuel_instant

    def set_wavebreaker_order(self, speed_limit: MetersPerSecond):
        if self.is_connected:
            self.target_speed = speed_limit
        else:
            self.target_speed = self.desired_speed