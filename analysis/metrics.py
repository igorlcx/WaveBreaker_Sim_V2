"""
WAVEBREAKER TWIN-ANALYTICS ENGINE
---------------------------------
Module d'analyse comparative post-simulation.
Génère le rapport final de performance (A/B Testing).

Correction : Normalisation des couleurs pour Matplotlib (0-255 -> 0.0-1.0).
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np
import logging
import seaborn as sns
from typing import List, Dict

from config import C
from simulation.road import Road

logger = logging.getLogger("WaveBreaker.Analytics")

class TwinTrafficRecorder:
    def __init__(self):
        self.records_chaos = []
        self.records_wb = []
        self.sample_rate = 2.0 
        self.last_record_time = -1.0

    def record_step(self, time: float, road_chaos: Road, road_wb: Road):
        if time - self.last_record_time >= self.sample_rate:
            self.last_record_time = time
            self._capture_road_state(time, road_chaos, self.records_chaos)
            self._capture_road_state(time, road_wb, self.records_wb)

    def _capture_road_state(self, time: float, road: Road, storage: list):
        for v in road.vehicles:
            storage.append({
                "time": round(time, 1),
                "pos_km": round(v.x / 1000.0, 3),
                "speed_kmh": round(v.v * 3.6, 1),
                "is_connected": v.is_connected
            })

    def generate_comparison_report(self, road_chaos: Road, road_wb: Road, filename="WaveBreaker_Final_Report.png"):
        logger.info("Generating Final Comparative Report...")

        df_chaos = pd.DataFrame(self.records_chaos)
        df_wb = pd.DataFrame(self.records_wb)
        
        if df_chaos.empty or df_wb.empty:
            logger.warning("Not enough data to generate report.")
            return

        # Downsampling
        max_pts = 100000
        step_c = max(1, len(df_chaos) // max_pts)
        step_w = max(1, len(df_wb) // max_pts)
        
        df_c_plot = df_chaos.iloc[::step_c]
        df_w_plot = df_wb.iloc[::step_w]

        # --- CONVERSION COULEURS (FIX CRASH) ---
        # Matplotlib veut du (R,G,B) entre 0 et 1
        color_chaos = tuple(c/255.0 for c in C.display.COLOR_SCENARIO_1)
        color_wb = tuple(c/255.0 for c in C.display.COLOR_SCENARIO_2)

        # Setup Graphique
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(3, 2, height_ratios=[3, 1, 1])
        
        # ZONE A : Time-Space Diagrams
        ax_ts_c = fig.add_subplot(gs[0, 0])
        ax_ts_w = fig.add_subplot(gs[0, 1])
        
        self._plot_time_space(ax_ts_c, df_c_plot, "SCÉNARIO 1 : CHAOS (Humains)", with_ylabel=True)
        self._plot_time_space(ax_ts_w, df_w_plot, f"SCÉNARIO 2 : WAVEBREAKER", with_ylabel=False)

        # ZONE B : Impact Écologique
        ax_eco = fig.add_subplot(gs[1, :])
        self._plot_eco_comparison(ax_eco, road_chaos, road_wb, color_chaos, color_wb)

        # ZONE C : Distribution Temps
        ax_hist = fig.add_subplot(gs[2, :])
        self._plot_travel_times(ax_hist, road_chaos, road_wb)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        logger.info(f"Report saved successfully: {filename}")
        plt.close()

    def _plot_time_space(self, ax, df, title, with_ylabel=False):
        scatter = ax.scatter(
            df['time'], df['pos_km'], 
            c=df['speed_kmh'], cmap='RdYlGn', 
            s=0.5, alpha=0.6, vmin=0, vmax=130
        )
        ax.set_title(title, fontsize=14, color='white', fontweight='bold')
        ax.set_ylim(0, C.road.length_km)
        ax.set_xlabel("Temps (s)")
        if with_ylabel: ax.set_ylabel("Position (km)")
        ax.axhline(y=C.sim.perturbation_pos, color='purple', linestyle='--', alpha=0.5, label='Zone Accident')
        ax.legend(loc='upper right')

    def _plot_eco_comparison(self, ax, r_c: Road, r_w: Road, col_c, col_w):
        labels = ['CO2 Total (kg)', 'Essence Totale (L)']
        chaos_vals = [r_c.metrics['total_co2_kg'], r_c.metrics['total_fuel_liters']]
        wb_vals = [r_w.metrics['total_co2_kg'], r_w.metrics['total_fuel_liters']]

        x = np.arange(len(labels))
        width = 0.35

        # Utilisation des couleurs normalisées
        rects1 = ax.bar(x - width/2, chaos_vals, width, label='Chaos', color=col_c)
        rects2 = ax.bar(x + width/2, wb_vals, width, label='WaveBreaker', color=col_w)

        ax.set_ylabel('Quantité')
        ax.set_title('Impact Écologique & Économique', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        for i, (c, w) in enumerate(zip(chaos_vals, wb_vals)):
            if c > 0:
                saving = ((c - w) / c) * 100
                txt = f"-{saving:.1f}%"
                ax.text(x[i] + width/2, w, txt, ha='center', va='bottom', color='white', fontweight='bold')

    def _plot_travel_times(self, ax, r_c: Road, r_w: Road):
        times_c = r_c.finished_travel_times
        times_w = r_w.finished_travel_times

        if not times_c or not times_w:
            ax.text(0.5, 0.5, "Pas assez de véhicules arrivés", ha='center', va='center', transform=ax.transAxes)
            return

        sns.kdeplot(times_c, ax=ax, fill=True, color='red', alpha=0.3, label=f"Chaos (Avg: {np.mean(times_c):.0f}s)")
        sns.kdeplot(times_w, ax=ax, fill=True, color='green', alpha=0.3, label=f"WaveBreaker (Avg: {np.mean(times_w):.0f}s)")
        ax.set_title("Distribution des Temps de Trajet", fontsize=12)
        ax.set_xlabel("Temps de parcours (s)")
        ax.legend()