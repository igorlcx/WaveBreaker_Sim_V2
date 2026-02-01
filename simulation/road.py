"""
WAVEBREAKER ROAD MANAGER
------------------------
Gère les véhicules et l'état de 'Crise' (Pénalité conso).
"""

import logging
from operator import attrgetter
from typing import List, Optional, Dict

from config import C
from core.vehicle import Vehicle
from core.infrastructure import SensorNetwork

class Road:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"WaveBreaker.Road.{name}")
        
        self.vehicles: List[Vehicle] = []
        self.sensors = SensorNetwork()
        self.time: float = 0.0
        self.frame_count: int = 0
        
        self.stats_total_vehicles_finished: int = 0
        self.stats_total_co2_kg: float = 0.0
        self.stats_total_fuel_liters: float = 0.0
        
        self.finished_travel_times: List[float] = []
        self._x_getter = attrgetter('x')
        
        # Flag activé par le Generator au moment de l'accident
        self.penalty_active = False 

    def add_vehicle(self, vehicle: Vehicle) -> None:
        vehicle.entry_time = self.time
        self.vehicles.append(vehicle)

    def update(self, dt: float) -> None:
        self.time += dt
        self.frame_count += 1
        
        self.vehicles.sort(key=self._x_getter, reverse=True)

        # === DÉCISION DU FACTEUR ===
        # Une fois activé, ce facteur restera à 1.3 tant que penalty_active est True
        current_factor = 1.45 if self.penalty_active else 1.0

        limit_m = C.road.length_m
        next_vehicles: List[Vehicle] = []
        
        count = len(self.vehicles)
        for i in range(count):
            veh = self.vehicles[i]
            
            lead_vehicle: Optional[Vehicle] = None
            if i > 0:
                potential_leader = self.vehicles[i-1]
                if (potential_leader.x - veh.x) < 1000.0:
                    lead_vehicle = potential_leader

            # Transmission du facteur au véhicule
            veh.update_dynamics(dt, lead_vehicle, emission_factor=current_factor)
            
            if veh.x < limit_m:
                next_vehicles.append(veh)
            else:
                self._archive_vehicle_stats(veh)

        self.vehicles = next_vehicles
        self.sensors.update(self.vehicles)

    def _archive_vehicle_stats(self, veh: Vehicle):
        self.stats_total_vehicles_finished += 1
        self.stats_total_co2_kg += veh.co2_total
        self.stats_total_fuel_liters += veh.fuel_total
        
        duration = self.time - veh.entry_time
        self.finished_travel_times.append(duration)

    @property
    def metrics(self) -> Dict[str, float]:
        current_active_co2 = sum(v.co2_total for v in self.vehicles)
        current_active_fuel = sum(v.fuel_total for v in self.vehicles)
        
        total_co2 = self.stats_total_co2_kg + current_active_co2
        total_fuel = self.stats_total_fuel_liters + current_active_fuel
        
        if self.finished_travel_times:
            avg_time = sum(self.finished_travel_times) / len(self.finished_travel_times)
        else:
            avg_time = 0.0
            
        avg_density = self.sensors.snapshot.densities.mean()

        return {
            "total_co2_kg": total_co2,
            "total_fuel_liters": total_fuel,
            "avg_travel_time": avg_time,
            "avg_density": avg_density,
            "vehicle_count": len(self.vehicles) + self.stats_total_vehicles_finished
        }