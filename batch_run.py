"""
WAVEBREAKER MONTE-CARLO RUNNER (HEADLESS)
-----------------------------------------
Module d'exécution batch pour validation statistique (Industrial Grade).
Lance N simulations en parallèle sans interface graphique pour générer
des intervalles de confiance sur les gains (CO2, Fuel, Temps).

Fonctionnalités :
- Multiprocessing (Utilisation de tous les cœurs CPU).
- Mode Headless (Pas de Pygame, pur calcul physique).
- Agrégation statistique (Pandas/Seaborn).
- Visualisation de la robustesse (Boxplots).

Auteur: WaveBreaker Lead Architect
Version: 1.0.0 (Monte-Carlo)
"""

import multiprocessing
import time
import logging
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from tqdm import tqdm

# Imports Core (Sans UI)
from config import C
from core.controller import WaveBreakerBrain
from simulation.road import Road
from simulation.generator import TrafficGenerator

# Configuration du Batch
SIMULATION_COUNT = 50       # Nombre de simulations à lancer
WB_PENETRATION_RATE = 0.20  # On teste la robustesse à 20%
MAX_DURATION_SEC = 2500.0   # Durée max d'une run (simulée)

def run_single_simulation(sim_id: int) -> Dict[str, float]:
    """
    Exécute une simulation complète en mode silencieux.
    Retourne les deltas de performance (Chaos vs WB).
    """
    # 1. Isolation de l'aléatoire
    # Chaque processus doit avoir une graine unique pour être reproductible
    random.seed(sim_id * 12345)
    np.random.seed(sim_id * 12345)
    
    # 2. Setup (Copie de main.py sans le Rendu)
    road_chaos = Road(f"Sim{sim_id}_Chaos")
    road_wb = Road(f"Sim{sim_id}_WB")
    brain = WaveBreakerBrain(active_scenario=True)
    generator = TrafficGenerator(road_chaos, road_wb, brain)
    generator.set_penetration_rate(WB_PENETRATION_RATE)
    
    # 3. Boucle Rapide (Pure Physique)
    current_time = 0.0
    dt = C.sim.dt
    
    while current_time < MAX_DURATION_SEC:
        generator.update(dt)
        road_chaos.update(dt)
        road_wb.update(dt)
        brain.process(road_wb.sensors.snapshot, road_wb.vehicles)
        current_time += dt

    # 4. Extraction des KPIs finaux
    m_chaos = road_chaos.metrics
    m_wb = road_wb.metrics
    
    # Calcul des gains relatifs (%)
    gain_co2 = 0.0
    gain_fuel = 0.0
    gain_time = 0.0
    
    if m_chaos['total_co2_kg'] > 0:
        gain_co2 = (m_chaos['total_co2_kg'] - m_wb['total_co2_kg']) / m_chaos['total_co2_kg'] * 100
        gain_fuel = (m_chaos['total_fuel_liters'] - m_wb['total_fuel_liters']) / m_chaos['total_fuel_liters'] * 100
    
    if m_chaos['avg_travel_time'] > 0:
        gain_time = (m_chaos['avg_travel_time'] - m_wb['avg_travel_time']) / m_chaos['avg_travel_time'] * 100
        
    return {
        "sim_id": sim_id,
        "gain_co2_pct": gain_co2,
        "gain_fuel_pct": gain_fuel,
        "gain_time_pct": gain_time,
        "vehicle_count": m_chaos['vehicle_count']
    }

def main_batch():
    print(f"\n🚀 LANCEMENT DU BATCH MONTE-CARLO ({SIMULATION_COUNT} Runs)")
    print(f"   Target WB Rate: {WB_PENETRATION_RATE*100}%")
    print(f"   CPUs disponibles: {multiprocessing.cpu_count()}")
    print("=" * 60)

    # Préparation des IDs
    sim_ids = list(range(SIMULATION_COUNT))
    results = []
    start_time = time.time()

    # Exécution Parallèle
    num_workers = max(1, multiprocessing.cpu_count() - 1)
    
    with multiprocessing.Pool(processes=num_workers) as pool:
        # imap_unordered pour le reporting temps réel avec tqdm
        for res in tqdm(pool.imap_unordered(run_single_simulation, sim_ids), total=SIMULATION_COUNT):
            results.append(res)

    duration = time.time() - start_time
    print(f"\n✅ Batch terminé en {duration:.1f}s")
    
    # --- ANALYSE & VISUALISATION ---
    if not results:
        print("Erreur: Aucun résultat généré.")
        return

    df = pd.DataFrame(results)
    
    print("\n--- RÉSULTATS STATISTIQUES ---")
    print(df[['gain_co2_pct', 'gain_fuel_pct', 'gain_time_pct']].describe())
    
    # Génération du Boxplot
    plt.style.use('dark_background')
    plt.figure(figsize=(10, 6))
    
    df_melt = df.melt(
        id_vars=['sim_id'], 
        value_vars=['gain_co2_pct', 'gain_fuel_pct', 'gain_time_pct'],
        var_name='Métrique', value_name='Gain (%)'
    )
    
    name_map = {
        'gain_co2_pct': 'Économie CO2', 
        'gain_fuel_pct': 'Économie Essence', 
        'gain_time_pct': 'Gain de Temps'
    }
    df_melt['Métrique'] = df_melt['Métrique'].map(name_map)
    
    sns.boxplot(x='Métrique', y='Gain (%)', data=df_melt, palette="viridis")
    sns.swarmplot(x='Métrique', y='Gain (%)', data=df_melt, color=".9", size=4, alpha=0.5)
    
    plt.title(f"Robustesse WaveBreaker (N={SIMULATION_COUNT}, Taux={WB_PENETRATION_RATE*100}%)", fontsize=14)
    plt.axhline(0, color='red', linestyle='--', alpha=0.5)
    plt.grid(True, axis='y', alpha=0.2)
    
    output_file = "WaveBreaker_Robustness_Analysis.png"
    plt.savefig(output_file, dpi=150)
    print(f"\n📊 Graphique de robustesse généré : {output_file}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main_batch()