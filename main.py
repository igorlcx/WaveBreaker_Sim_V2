"""
WAVEBREAKER TWIN-RUN LAUNCHER (DPI FIXED)
-----------------------------------------
Point d'entrée corrigé avec gestion DPI Windows pour éviter le zoom flou.
"""

import pygame
import logging
import sys
import os
import ctypes # <--- AJOUT CRITIQUE

# --- FIX WINDOWS SCALING (Empêche le zoom automatique) ---
try:
    # Indique au système que l'application gère sa propre résolution
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from config import C
from core.controller import WaveBreakerBrain
from simulation.road import Road
from simulation.generator import TrafficGenerator
from ui.renderer import TwinRenderer
from ui.dashboard import Dashboard
from analysis.metrics import TwinTrafficRecorder

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Main")

MAX_SIMULATION_TIME = 3000.0 

def get_user_input() -> float:
    print("\n" + "="*60)
    print("  WAVEBREAKER SIMULATION ENGINE v3.5 (HD Native)")
    print("="*60)
    print("Configuration :")
    print("  - Route : 50 km")
    print(f"  - Accident : Km {C.sim.perturbation_pos} à T={C.sim.perturbation_time:.0f}s")
    print(f"  - Durée Auto : ~50 secondes réelles")
    print("-" * 60)
    
    while True:
        try:
            val = input(">> Entrez le taux de pénétration WaveBreaker (0-100) : ")
            rate = float(val)
            if 0 <= rate <= 100:
                return rate / 100.0
            print("Erreur : 0-100.")
        except ValueError:
            print("Erreur : Entrée invalide.")

def main():
    wb_rate = get_user_input()
    
    # SETUP
    road_chaos = Road("Scenario_Chaos")
    road_wb = Road("Scenario_WaveBreaker")
    brain = WaveBreakerBrain(active_scenario=True)
    generator = TrafficGenerator(road_chaos, road_wb, brain)
    generator.set_penetration_rate(wb_rate)
    recorder = TwinTrafficRecorder()

    # UI
    renderer = TwinRenderer(road_chaos, road_wb)
    dashboard = Dashboard(C.display.screen_size)
    clock = pygame.time.Clock()

    running = True
    STEPS_PER_FRAME = 4

    while running:
        clock.tick(C.sim.fps) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Auto-Stop
        if road_chaos.time >= MAX_SIMULATION_TIME:
            logger.info("⏱️  Fin de la session (3000s).")
            running = False

        # Boucle Physique Calibrée
        sim_step = C.sim.dt
        for _ in range(STEPS_PER_FRAME):
            generator.update(sim_step)
            road_chaos.update(sim_step)
            road_wb.update(sim_step)
            brain.process(road_wb.sensors.snapshot, road_wb.vehicles, road_wb.time)
            recorder.record_step(road_chaos.time, road_chaos, road_wb)

        # UI
        dashboard.update(road_chaos.metrics, road_wb.metrics)
        real_fps = clock.get_fps()
        renderer.render(real_fps, 60.0) 
        dashboard.draw(renderer.screen)
        
        pygame.display.flip()

    pygame.quit()
    
    logger.info("Génération du rapport...")
    try:
        recorder.generate_comparison_report(road_chaos, road_wb)
        logger.info("✅ RAPPORT GÉNÉRÉ : 'WaveBreaker_Final_Report.png'")
        
        if sys.platform == 'win32':
            os.system("start WaveBreaker_Final_Report.png")
            
    except Exception as e:
        logger.error(f"Erreur rapport: {e}")

    sys.exit()

if __name__ == "__main__":
    main()
