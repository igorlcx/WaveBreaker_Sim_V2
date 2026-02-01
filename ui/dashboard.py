"""
WAVEBREAKER DASHBOARD (DELL G16 OPTIMIZED)
------------------------------------------
- Résolution cible : 2560x1600.
- Widgets agrandis pour la lisibilité haute résolution.
- Polices proportionnelles pour éviter l'effet "texte minuscule".
"""

import pygame
from collections import deque
from config import C

# Couleurs Dashboard
COLOR_BG_WIDGET = (25, 27, 32, 245) 
COLOR_BORDER = (80, 85, 90)
COLOR_TEXT_V_DIM = (120, 120, 120)
COLOR_TEXT_DIM = (180, 180, 180)

class ComparativeChart:
    def __init__(self, title, unit, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.unit = unit
        
        self.history_len = w // 2
        self.data_chaos = deque(maxlen=self.history_len)
        self.data_wb = deque(maxlen=self.history_len)
        self.max_val_seen = 1.0
        
        # --- POLICES AGRANDIES POUR G16 ---
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_val = pygame.font.SysFont("Consolas", 18)
        self.font_delta = pygame.font.SysFont("Segoe UI", 28, bold=True)

    def push(self, val_chaos, val_wb):
        self.data_chaos.append(val_chaos)
        self.data_wb.append(val_wb)
        current_max = max(val_chaos, val_wb)
        if current_max > self.max_val_seen:
            self.max_val_seen = current_max

    def draw(self, surface):
        # Fond Opaque
        bg_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg_surf.fill(COLOR_BG_WIDGET)
        surface.blit(bg_surf, self.rect.topleft)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, 2) # Bordure plus épaisse (2px)

        # Textes et KPI
        if self.data_chaos:
            last_c = self.data_chaos[-1]
            last_w = self.data_wb[-1]
            
            saving = 0.0
            if last_c > 0.1: saving = ((last_c - last_w) / last_c) * 100.0
                
            header = f"{self.title}"
            vals = f"CHAOS: {last_c:.1f}{self.unit}  vs  WB: {last_w:.1f}{self.unit}"
            delta = f"SAVING: {saving:+.1f}%"
            
            t_surf = self.font_title.render(header, True, COLOR_TEXT_DIM)
            v_surf = self.font_val.render(vals, True, COLOR_TEXT_V_DIM)
            
            # Couleur dynamique du gain
            col_save = (46, 204, 113) if saving >= 0 else (231, 76, 60)
            d_surf = self.font_delta.render(delta, True, col_save)
            
            # Positionnement sur G16 (Margins augmentées)
            surface.blit(t_surf, (self.rect.x + 20, self.rect.y + 15))
            surface.blit(v_surf, (self.rect.x + 20, self.rect.y + 50))
            surface.blit(d_surf, (self.rect.right - d_surf.get_width() - 20, self.rect.y + 20))

        # Graphiques
        if len(self.data_chaos) < 2: return

        # On laisse de la place pour les textes en haut (offset 80px)
        scale_x = self.rect.w / self.history_len
        scale_y = (self.rect.h - 90) / (self.max_val_seen if self.max_val_seen > 0 else 1)
        base_y = self.rect.bottom - 15

        pts_chaos = []
        for i, val in enumerate(self.data_chaos):
            pts_chaos.append((self.rect.x + i*scale_x, base_y - val*scale_y))
            
        pts_wb = []
        for i, val in enumerate(self.data_wb):
            pts_wb.append((self.rect.x + i*scale_x, base_y - val*scale_y))

        # Courbes plus épaisses pour la haute résolution
        if len(pts_chaos) > 1:
            pygame.draw.lines(surface, (231, 76, 60), False, pts_chaos, 3)
        if len(pts_wb) > 1:
            pygame.draw.lines(surface, (46, 204, 113), False, pts_wb, 3)

class Dashboard:
    def __init__(self, screen_size):
        self.width, self.height = screen_size
        
        # Dimensions AGRANDIES pour occuper l'espace du G16
        # Largeur passée de 450 à 600px | Hauteur de 200 à 280px
        w = 600
        h = 280
        margin = 50
        
        # Aligné à droite
        start_x = self.width - w - margin
        start_y = 60 
        
        self.chart_fuel = ComparativeChart("FUEL CONSUMPTION", "L", start_x, start_y, w, h)
        # Espacement augmenté entre les widgets
        self.chart_co2 = ComparativeChart("CO2 EMISSIONS", "kg", start_x, start_y + h + 40, w, h)

    def update(self, metrics_chaos, metrics_wb):
        self.chart_fuel.push(metrics_chaos['total_fuel_liters'], metrics_wb['total_fuel_liters'])
        self.chart_co2.push(metrics_chaos['total_co2_kg'], metrics_wb['total_co2_kg'])

    def draw(self, surface):
        self.chart_fuel.draw(surface)
        self.chart_co2.draw(surface)