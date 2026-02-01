"""
WAVEBREAKER INTELLIGENCE CORE (DYNAMIC BOQ EDITION - FIXED)
---------------------------------------------------
Stratégie : Eco-Glide Adaptatif avec détection de queue de bouchon (BOQ).
Correction : Gestion dynamique de l'attribut de vitesse du SensorSnapshot.
"""

import numpy as np
import logging
from typing import List
from config import C
from core.vehicle import Vehicle
from core.infrastructure import SensorSnapshot

logger = logging.getLogger("WaveBreaker.Brain")

class WaveBreakerBrain:
    def __init__(self, active_scenario: bool = True):
        self.active = active_scenario 
        self.incident_active = False
        self.incident_pos_m = 0.0
        self.preshot_duration = 400.0 
        self.trigger_time = 0.0
        self.num_segments = C.road.num_segments
        self._current_speed_map = np.full(self.num_segments, C.physics.desired_speed, dtype=np.float64)

        if self.active:
            logger.info(f"WaveBreaker Brain online (PRESHOT {self.preshot_duration}s).")

    def set_incident_state(self, active: bool, end_time: float, pos_m: float):
        if active and not self.incident_active:
            self.trigger_time = 0.0 
        self.incident_active = active
        self.incident_pos_m = pos_m

    def process(self, sensor_data: SensorSnapshot, vehicles: List[Vehicle], current_time: float) -> None:
        if not self.active or not self.incident_active:
            self._current_speed_map.fill(C.physics.desired_speed)
            self.trigger_time = 0.0
            self._dispatch_orders(vehicles)
            return

        if self.trigger_time == 0.0:
            self.trigger_time = current_time
            logger.warning("IA : Mode ECO-GLIDE dynamique activé (V2X).")

        # 1. TEMPS RESTANT (L'entonnoir temporel)
        elapsed = current_time - self.trigger_time
        time_left = max(1.0, self.preshot_duration - elapsed)

        # 2. DÉTECTION DE LA QUEUE DU BOUCHON (BOQ) - FIX ATTRIBUTE ERROR
        # On vérifie quel attribut est disponible dans SensorSnapshot
        speeds = getattr(sensor_data, 'speeds', getattr(sensor_data, 'avg_speeds', None))
        
        if speeds is None:
            # Fallback si aucun attribut n'est trouvé pour éviter le crash
            boq_pos = self.incident_pos_m
        else:
            jam_threshold = 20.0 / 3.6
            boq_pos = self.incident_pos_m 
            
            # Parcours inverse pour trouver la queue du bouchon
            for i in range(len(speeds) - 1, -1, -1):
                seg_pos = i * C.road.sensor_spacing
                if seg_pos < self.incident_pos_m:
                    if speeds[i] < jam_threshold:
                        boq_pos = seg_pos
                    elif speeds[i] > (60.0/3.6) and boq_pos < self.incident_pos_m:
                        break

        # 3. CALCUL DES VITESSES CIBLES
        segment_positions = np.arange(self.num_segments) * C.road.sensor_spacing
        distances_to_target = boq_pos - segment_positions
        upstream_mask = distances_to_target > 0

        # Vitesse ballistique optimale
        v_optimal = distances_to_target[upstream_mask] / time_left
        
        # BRIDES DE SÉCURITÉ ET EFFET VISUEL (WAW EFFECT)
        # On bride à 80 km/h (au lieu de 130) pour que le passage au VERT NÉON soit immédiat
        v_max_crisis = 80.0 / 3.6 
        v_min_safety = 25.0 / 3.6 
        
        v_clamped = np.clip(v_optimal, v_min_safety, v_max_crisis)

        self._current_speed_map.fill(C.physics.desired_speed) 
        self._current_speed_map[upstream_mask] = v_clamped 
        
        self._dispatch_orders(vehicles)

    def _dispatch_orders(self, vehicles: List[Vehicle]):
        seg_len = C.road.sensor_spacing
        for v in vehicles:
            if v.is_connected:
                idx = int(v.x / seg_len)
                if 0 <= idx < self.num_segments:
                    # Application immédiate de la consigne IA
                    v.set_wavebreaker_order(self._current_speed_map[idx])