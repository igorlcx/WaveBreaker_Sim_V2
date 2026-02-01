"""
WAVEBREAKER HIGH-RES RENDERER (WAW EFFECT EDITION)
--------------------------------------------------
Optimisé pour Dell G16 (2560x1600).
- IA WB : Barres ultra-épaisses (8px) Vert Néon + Halo.
- Humains : Traits fins (2px) standards.
- Dashboard : Polices agrandies et métriques lisibles.
"""

import pygame
from typing import Tuple
from config import C
from simulation.road import Road
from core.vehicle import Vehicle

# Palette de couleurs synchronisée avec DisplayConfig et Analytics
COLOR_BG = (15, 17, 21)
COLOR_ROAD_BG = (25, 27, 30) 
COLOR_LANE_MARKER = (60, 65, 70)
COLOR_ACCIDENT_CAR = (255, 0, 255)

class TwinRenderer:
    def __init__(self, road_chaos: Road, road_wb: Road):
        pygame.init()
        # On utilise la taille native configurée (2560x1500 recommandé pour G16)
        self.width, self.height = C.display.screen_size
        self.road_chaos = road_chaos
        self.road_wb = road_wb
        
        # Mode matériel pour la fluidité en haute résolution
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption(f"WaveBreaker High-Res | {self.width}x{self.height}")
        
        # --- INITIALISATION DES POLICES (Fix AttributeError) ---
        self.font_title = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_alert = pygame.font.SysFont("Arial Black", 72, bold=True)
        self.font_label = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_stats = pygame.font.SysFont("Courier New", 26, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 14)
        
        # --- LAYOUT POUR DELL G16 ---
        self.viewport_h = 420 
        self.spacing = 100
        
        # Centrage vertical des deux blocs de route
        total_h = (self.viewport_h * 2) + self.spacing
        offset_y = (self.height - total_h) // 2
        
        self.rect_chaos = pygame.Rect(0, offset_y, self.width, self.viewport_h)
        self.rect_wb = pygame.Rect(0, offset_y + self.viewport_h + self.spacing, self.width, self.viewport_h)
        
        # Échelle : 40km étalés sur toute la largeur de l'écran (ex: 2560px)
        self.scale_x = self.width / C.road.length_m

    def render(self, fps: float, sim_speed: float):
        self.screen.fill(COLOR_BG)
        self._draw_header(fps, sim_speed)
        
        # Dessin des deux scénarios (Couleurs liées à DisplayConfig pour Analytics)
        self._draw_road_viewport(self.road_chaos, self.rect_chaos, "SCENARIO A : HUMANS (CHAOS)", C.display.COLOR_SCENARIO_1)
        self._draw_road_viewport(self.road_wb, self.rect_wb, "SCENARIO B : WAVEBREAKER (AI)", C.display.COLOR_SCENARIO_2)
        
        pygame.display.flip()

    def _draw_header(self, fps: float, sim_speed: float):
        # Utilisation de COLOR_TEXT de la config
        title = self.font_title.render(f"SIMULATION TIME: {self.road_chaos.time:.1f}s", True, C.display.COLOR_TEXT)
        self.screen.blit(title, (50, 40))
        
        info_txt = f"WARP: x{sim_speed:.0f} | FPS: {fps:.0f}"
        info = self.font_label.render(info_txt, True, (127, 140, 141))
        self.screen.blit(info, (self.width - info.get_width() - 50, 45))

    def _draw_road_viewport(self, road: Road, rect: pygame.Rect, label: str, accent_color: Tuple[int,int,int]):
        # Fond du viewport
        pygame.draw.rect(self.screen, (25, 27, 31), rect)
        
        # Bande de roulement
        road_vis_h = 130
        road_y = rect.centery - (road_vis_h // 2)
        pygame.draw.rect(self.screen, COLOR_ROAD_BG, (0, road_y, self.width, road_vis_h))
        pygame.draw.line(self.screen, COLOR_LANE_MARKER, (0, rect.centery), (self.width, rect.centery), 1)

        # --- VÉHICULES ---
        accident_detected = False
        
        for v in road.vehicles:
            sx = int(v.x * self.scale_x)
            
            # Cas du véhicule accidenté (Immobile au Km 30)
            if v.target_speed == 0.0 and v.v == 0.0:
                accident_detected = True
                pygame.draw.circle(self.screen, COLOR_ACCIDENT_CAR, (sx, rect.centery), 22)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, rect.centery), 22, 3)
                continue

            if v.is_connected:
                # --- EFFET IA WAVEBREAKER : SOBRE ET PUISSANT ---
                color = C.display.COLOR_IA_NEON # Vert brillant
                width = 8            # Épaisseur maximale pour G16
                height_mod = 45      # Dépasse largement de la route
                # Le rond central a été supprimé ici
            else:
                # --- HUMAINS STANDARDS (Traits fins) ---
                width = 2
                height_mod = 18
                if v.v < (15.0 / 3.6): 
                    color = C.display.COLOR_SCENARIO_1 # Rouge Chaos
                elif v.v < (70.0 / 3.6): 
                    color = (241, 196, 15) # Jaune/Orange lent
                else: 
                    color = (200, 200, 200) # Blanc flux

            # Dessin de la barre verticale
            pygame.draw.line(self.screen, color, (sx, rect.centery - height_mod), (sx, rect.centery + height_mod), width)

        # Overlay Alerte Clignotante
        if accident_detected and int(road.time * 2) % 2 == 0:
            alert_surf = self.font_alert.render("Perturbation !", True, C.display.COLOR_SCENARIO_1)
            text_rect = alert_surf.get_rect(center=(self.width // 2, rect.top + 80))
            self.screen.blit(alert_surf, text_rect)

        # Dashboard intégré au Viewport
        pygame.draw.rect(self.screen, accent_color, (rect.x, rect.y, 10, rect.height))
        lbl_surf = self.font_label.render(label, True, accent_color)
        self.screen.blit(lbl_surf, (40, rect.y + 30))
        
        m = road.metrics
        stats_txt = f"CO2: {m['total_co2_kg']:.1f}kg  |  FUEL: {m['total_fuel_liters']:.1f}L  |  TRAFFIC: {m['vehicle_count']} units"
        stats_surf = self.font_stats.render(stats_txt, True, C.display.COLOR_TEXT)
        self.screen.blit(stats_surf, (40, rect.bottom - 60))