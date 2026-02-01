"""
WAVEBREAKER CONFIGURATION MODULE
--------------------------------
Fichier central de paramètres.
Version: 3.11 (Km 30 & Trafic Aéré)
"""

from dataclasses import dataclass, field
from typing import Tuple
from enum import Enum, auto

class ScenarioType(Enum):
    CHAOS = auto()
    WB_ACTIVE = auto()

@dataclass(frozen=True)
class PhysicsParams:
    desired_speed: float = 130.0 / 3.6
    
    # --- MODIF ICI : DISTANCE DE SÉCURITÉ ---
    # 1.6 secondes = ~57 mètres à 130km/h (Visuellement "proche" mais pas "collé")
    time_headway: float = 3          
    
    min_spacing: float = 3.0           
    max_accel: float = 2.0             
    comfort_decel: float = 3.0         
    accel_exponent: float = 4.0

    # Émissions
    co2_idle_emission: float = 0.8     
    co2_speed_factor: float = 0.05
    co2_accel_factor: float = 1.5
    accel_boost_factor: float = 1.0       
    fuel_conversion_factor: float = 1.0 / 2.3

@dataclass(frozen=True)
class SimSettings:
    dt: float = 0.25           
    fps: int = 60
    time_scale_default: float = 60.0 
    # --- MODIF ICI : DENSITÉ ---
    nominal_flow: float = 600.0 # On réduit le flux global
    
    perturbation_time: float = 1200.0 
    
    # --- MODIF ICI : POSITION ACCIDENT ---
    perturbation_pos: float = 30.0   # Accident repoussé au Km 30

@dataclass(frozen=True)
class VehicleSpecs:
    length: float = 5.0
    width: float = 2.0
    max_speed_ms: float = 180.0 / 3.6

@dataclass(frozen=True)
class RoadSpecs:
    length_km: float = 50.0
    lanes: int = 1
    sensor_spacing: float = 1000.0
    
    @property
    def length_m(self) -> float:
        return self.length_km * 1000.0
    
    @property
    def num_segments(self) -> int:
        return int(self.length_m / self.sensor_spacing)

@dataclass(frozen=True)
class WaveBreakerConfig:
    Kp: float = 0.2
    Ki: float = 0.0
    Kd: float = 10.0
    sensor_range: float = 1000.0
    target_density: float = 30.0
    look_ahead_distance: float = 3000.0

@dataclass(frozen=True)

class DisplayConfig:
    # Résolution native Dell G16 (ajustée pour la barre des tâches)
    screen_size: Tuple[int, int] = (2560, 1500) 
    
    # Couleurs de fond
    COLOR_BG: Tuple[int,int,int] = (15, 17, 21)
    COLOR_ROAD_BG: Tuple[int,int,int] = (25, 27, 30)
    
    # Couleurs Scénarios (Attendues par Analytics et Renderer)
    COLOR_SCENARIO_1: Tuple[int,int,int] = (231, 76, 60) # Rouge Chaos
    COLOR_SCENARIO_2: Tuple[int,int,int] = (46, 204, 113) # Vert WB
    
    # Couleurs UI
    COLOR_TEXT: Tuple[int,int,int] = (236, 240, 241)
    COLOR_IA_NEON: Tuple[int,int,int] = (0, 255, 150) # Vert brillant pour le "WAW"

@dataclass(frozen=True)
class GlobalConfig:
    physics: PhysicsParams = field(default_factory=PhysicsParams)
    vehicle: VehicleSpecs = field(default_factory=VehicleSpecs)
    road: RoadSpecs = field(default_factory=RoadSpecs)
    wavebreaker: WaveBreakerConfig = field(default_factory=WaveBreakerConfig)
    sim: SimSettings = field(default_factory=SimSettings)
    display: DisplayConfig = field(default_factory=DisplayConfig)

C = GlobalConfig()


