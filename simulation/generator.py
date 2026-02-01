"""
WAVEBREAKER GENERATOR V13 (STRESS FACTOR EDITION)
-------------------------------------------------
- Déclenchement : T >= 1200s au Km 30.
- Durée du crash : 400s.
- Stress Factor : x1,3 maintenu sur Chaos après l'impact.
"""

import random
import logging
from config import C
from core.vehicle import Vehicle

logger = logging.getLogger("WaveBreaker.Generator")

class TrafficGenerator:
    def __init__(self, road_chaos, road_wb, brain):
        self.road_chaos = road_chaos
        self.road_wb = road_wb
        self.brain = brain
        
        self.vehicle_id_counter = 0
        self.wb_penetration_rate = 0.0
        self.next_spawn_time = 0.0
        
        self.incident_triggered = False
        self.incident_active = False
        self.crash_start_time = 0.0
        self.incident_duration = 400.0 

    def set_penetration_rate(self, rate_decimal: float):
        """Définit le ratio de véhicules connectés (0.0 à 1.0)."""
        self.wb_penetration_rate = rate_decimal
        logger.info(f"Taux d'IA activé : {self.wb_penetration_rate*100:.0f}%")

    def update(self, dt: float):
        current_time = self.road_chaos.time
        
        # 1. Injection de trafic constante (Flux aéré)
        if current_time >= self.next_spawn_time:
            self._spawn_twin_vehicles()
            self.next_spawn_time = current_time + (3600.0 / C.sim.nominal_flow)

        # 2. Déclenchement spatial et temporel
        if not self.incident_triggered and current_time >= C.sim.perturbation_time:
            for v in self.road_chaos.vehicles:
                if v.x >= C.sim.perturbation_pos * 1000.0:
                    self._trigger_crash(v.id, current_time)
                    self.incident_triggered = True
                    self.incident_active = True
                    self.crash_start_time = current_time
                    break

        # 3. Libération automatique
        if self.incident_active and current_time >= (self.crash_start_time + self.incident_duration):
            self._release_crash()

    def _trigger_crash(self, victim_id, time):
        """Active l'accident et le malus de stress sur Chaos."""
        # Active le facteur x1,3 dans road_chaos.update()
        self.road_chaos.penalty_active = True
        
        # Informe le cerveau WB pour lancer l'Eco-Glide (Preshot)
        self.brain.set_incident_state(True, time + self.incident_duration, C.sim.perturbation_pos * 1000.0)
        
        for road in [self.road_chaos, self.road_wb]:
            for v in road.vehicles:
                if v.id == victim_id:
                    v.v = 0.0
                    v.target_speed = 0.0
                    v.x = C.sim.perturbation_pos * 1000.0
        
        logger.warning(f"💥 IMPACT à T={time:.1f}s au Km {C.sim.perturbation_pos}")

    def _release_crash(self):
        """Libère la route mais maintient le stress sur Chaos."""
        self.incident_active = False
        
        # OPTIONNEL : Commenter la ligne suivante pour garder le malus x1,3 
        # sur Chaos même après la fin de l'accident (effet psychologique)
        # self.road_chaos.penalty_active = False 
        
        self.brain.set_incident_state(False, 0, 0)
        
        for road in [self.road_chaos, self.road_wb]:
            for v in road.vehicles:
                if v.v < 1.0: 
                    v.target_speed = v.desired_speed
                    
        logger.info(f"✅ Route libérée.")

    def _spawn_twin_vehicles(self):
        """Génère des véhicules identiques (Jumeaux numériques)."""
        self.vehicle_id_counter += 1
        v_init = C.physics.desired_speed
        
        self.road_chaos.add_vehicle(Vehicle(self.vehicle_id_counter, 0.0, v_init, v_init, False))
        
        is_wb = random.random() < self.wb_penetration_rate
        self.road_wb.add_vehicle(Vehicle(self.vehicle_id_counter, 0.0, v_init, v_init, is_wb))