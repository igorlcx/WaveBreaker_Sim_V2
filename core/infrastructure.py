"""
WAVEBREAKER SENSOR NETWORK
--------------------------
Module d'infrastructure intelligente (IoT).
Simule un réseau de capteurs inductifs ou de caméras le long de la route.

Optimisations :
- Agrégation vectorielle via NumPy (bincount) pour performance O(1) relative au nombre de segments.
- Gestion robuste des divisions par zéro (segments vides).
- Architecture 'Snapshot' immuable pour thread-safety potentiel.

Auteur: WaveBreaker Lead Architect
Version: 3.0.0 (Vectorized IoT)
"""

import numpy as np
from dataclasses import dataclass
from typing import List
from numpy.typing import NDArray

from config import C
from core.vehicle import Vehicle

@dataclass(frozen=True)
class SensorSnapshot:
    """
    DTO (Data Transfer Object) immuable représentant l'état de la route à l'instant T.
    Utilisé par le Contrôleur (IA) et le Dashboard (UI).
    """
    densities: NDArray[np.float64]   # Densité (veh/km) par segment
    mean_speeds: NDArray[np.float64] # Vitesse moyenne (m/s) par segment
    occupancy: NDArray[np.int64]     # Nombre brut de véhicules par segment

class SensorNetwork:
    """
    Gestionnaire des capteurs physiques.
    Mappe les positions continues (float) vers des segments discrets (bins).
    """

    def __init__(self):
        # Configuration topologique récupérée de C.road
        self.num_segments = C.road.num_segments
        self.segment_len = C.road.sensor_spacing
        
        # Initialisation de l'état vide (Zero-State)
        self._snapshot = SensorSnapshot(
            densities=np.zeros(self.num_segments, dtype=np.float64),
            mean_speeds=np.full(self.num_segments, C.vehicle.max_speed_ms, dtype=np.float64),
            occupancy=np.zeros(self.num_segments, dtype=np.int64)
        )

    def update(self, vehicles: List[Vehicle]) -> None:
        """
        Scan de la route et mise à jour des métriques.
        Cette méthode doit être ultra-rapide (appelée à chaque tick physique).
        """
        if not vehicles:
            self._reset_state()
            return

        # 1. EXTRACTION VECTORIELLE (Bottleneck potentiel en Python pur -> List Comp est le plus rapide)
        # On extrait les scalaires des objets Vehicle
        positions = np.array([v.x for v in vehicles], dtype=np.float64)
        speeds = np.array([v.v for v in vehicles], dtype=np.float64)

        # 2. DISCRÉTISATION SPATIALE (Binning)
        # On calcule l'index du segment pour chaque véhicule : idx = floor(x / segment_len)
        segment_indices = (positions // self.segment_len).astype(np.int64)

        # Filtrage des hors-limites (Sécurité)
        # Au cas où un véhicule dépasse légèrement 50km avant d'être garbage collected
        valid_mask = (segment_indices >= 0) & (segment_indices < self.num_segments)
        segment_indices = segment_indices[valid_mask]
        speeds = speeds[valid_mask]

        if len(segment_indices) == 0:
            self._reset_state()
            return

        # 3. AGRÉGATION (NumPy Magic)
        # np.bincount compte le nombre d'occurrences de chaque index -> Occupancy
        counts = np.bincount(segment_indices, minlength=self.num_segments)

        # Calcul des densités : (N / L_km)
        # segment_len est en mètres, on divise par 1000 pour avoir des km
        densities = counts / (self.segment_len / 1000.0)

        # Somme des vitesses par segment (Weighted bincount)
        speed_sums = np.bincount(segment_indices, weights=speeds, minlength=self.num_segments)

        # 4. CALCUL DES MOYENNES (Gestion division par zéro)
        # Là où count > 0 : Mean = Sum / Count
        # Là où count == 0 : Mean = V_free (Vitesse limite)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            calculated_means = speed_sums / counts
            # On remplace les NaNs (0/0) par la vitesse libre
            mean_speeds = np.where(counts > 0, calculated_means, C.vehicle.max_speed_ms)

        # 5. PUBLICATION DU SNAPSHOT
        self._snapshot = SensorSnapshot(
            densities=densities,
            mean_speeds=mean_speeds,
            occupancy=counts
        )

    def _reset_state(self):
        """Remet les capteurs à zéro (route vide)."""
        self._snapshot = SensorSnapshot(
            densities=np.zeros(self.num_segments),
            mean_speeds=np.full(self.num_segments, C.vehicle.max_speed_ms),
            occupancy=np.zeros(self.num_segments, dtype=np.int64)
        )

    @property
    def snapshot(self) -> SensorSnapshot:
        """Accès en lecture seule à l'état courant."""
        return self._snapshot