# -*- coding: utf-8 -*-
import math
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy 
from game.settings import settings
from game.config import BASE_TILE_SIZE
from game.pathfinder import get_walkable_grid, _pixel_to_tile, _tile_center

class Arakwa(Enemy):
    """Ennemi araignee capable de sauter par-dessus les obstacles."""
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = settings.base_speed * 0.95
        self._pv_max = 3
        self.pv_main = self._pv_max
        self.aggro_range = settings.tile_size * 12
        self.damage = 1
        self.give_stun = 0
        
        self.hitbox_offset_y = 3/BASE_TILE_SIZE
        self.hitbox_height = settings.tile_size * 0.75
        
        self.loot = [
            ("pomme", 0.20),
            ("mana", 0.05)
        ]

        # --- GESTION DES SPRITES ---
        self.sprite_normal = QPixmap("assets/enemies/arakwa/arakwa.png").scaled(
            settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
        )
        self.sprite_pre_jump = QPixmap("assets/enemies/arakwa/arakwa_pre_jump.png").scaled(
            settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
        )
        self.sprite_jump = QPixmap("assets/enemies/arakwa/arakwa_jump.png").scaled(
            settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
        )

        # Assigne les sprites initiaux
        self.set_sprites(self.sprite_normal)
        
        self.death_cry = "snd_death_arakwa"

        # --- ETATS DE SAUT ---
        self.tile_max_saut = 3
        
        self.state = "NORMAL" # NORMAL, PRE_JUMP, JUMPING, LANDING
        self.jump_timer = 0.0
        
        self.jump_start_x = 0
        self.jump_start_y = 0
        self.jump_target_x = 0
        self.jump_target_y = 0
        
        self.jump_check_timer = 0.0
        
        # secu anti bloquage
        self.stuck_timer = 0.0
        self.last_pos = (x, y)

    def set_sprites(self, pixmap):
        self.sprites = {
            "down": pixmap,
            "up": pixmap,
            "left": pixmap,
            "right": pixmap
        }

    def _get_line_tiles(self, x0, y0, x1, y1):
        """Algorithme de Bresenham pour recuperer les cases entre deux points."""
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            points.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return points
    
    
    def check_for_jump(self, dt, scene,forced = False):
        """Verifie si un detour est trop long ou si l'ennemi est bloque pour declencher un saut."""
        if not self.target:
            return

        self.jump_check_timer += dt
        if not forced and self.jump_check_timer < 0.3:
            return
        self.jump_check_timer = 0.0
        
        if forced:
            self.try_execute_jump(scene, bypass_ratio=True)
            return

        # CALCUL DES DISTANCES
        direct_distance = math.hypot(self.target.x - self.x, self.target.y - self.y)
        
        # cas ou il n'y a pas de chemin
        if not self.path or len(self.path) == 0:
            self.try_execute_jump(scene)
            return

        # cas ou il y a un chemin : on calcule sa longueur
        path_distance = math.hypot(self.path[0][0] - self.x, self.path[0][1] - self.y)
        for i in range(len(self.path) - 1):
            p1 = self.path[i]
            p2 = self.path[i+1]
            path_distance += math.hypot(p2[0] - p1[0], p2[1] - p1[1])

        # comparaison du détour
        # plus le facteur est eleve a droite, plus il va privilegier pathfinding
        if path_distance > direct_distance * 1.5:
            self.try_execute_jump(scene)

    def try_execute_jump(self, scene,bypass_ratio=False):
        """Analyse si un saut est physiquement possible au-dessus d'un obstacle."""
        grid = get_walkable_grid(scene.room_data)
        h = len(grid)
        w = len(grid[0]) if h > 0 else 0

        start_col, start_row = _pixel_to_tile(self.x, self.y, settings.tile_size)
        target_col, target_row = _pixel_to_tile(self.target.x, self.target.y, settings.tile_size)

        line = self._get_line_tiles(start_col, start_row, target_col, target_row)
        
        wall_count = 0
        jump_target_tile = None
        
        for i, (c, r) in enumerate(line):
            if not (0 <= c < w and 0 <= r < h): 
                break
            
            if not grid[r][c]: 
                wall_count += 1
            else: 
                if wall_count > 0: 
                    if wall_count <= self.tile_max_saut:
                        jump_target_tile = (c, r)
                    break 
                elif bypass_ratio and wall_count == 0 and (c != start_col or r != start_row):
                    jump_target_tile = (c, r)
                    break
                
        if jump_target_tile:
            tx, ty = _tile_center(jump_target_tile[0], jump_target_tile[1], settings.tile_size)
            self.start_jump(tx, ty)
            
    def start_jump(self, target_x, target_y):
        self.state = "PRE_JUMP"
        self.jump_timer = 1.0
        self.set_sprites(self.sprite_pre_jump)
        
        self.jump_start_x = self.x
        self.jump_start_y = self.y
        self.jump_target_x = target_x
        self.jump_target_y = target_y

    def update(self, dt, scene):
        # prio au stun et knockback
        if self.kb_active or self.is_stunned:
            super().update(dt, scene)
            return

        if self.state == "NORMAL":
            dist_moved = math.hypot(self.x - self.last_pos[0], self.y - self.last_pos[1])
            
            if dist_moved < 0.1:
                self.stuck_timer += dt
            else:
                self.stuck_timer = 0.0
            
            self.last_pos = (self.x, self.y)

            if self.stuck_timer >= 1.5:
                self.check_for_jump(dt, scene, forced=True)
                self.stuck_timer = 0.0
            else:
                # Comportement A* classique
                super().update(dt, scene)
                self.check_for_jump(dt, scene)

        elif self.state == "PRE_JUMP":
            self.jump_timer -= dt
            if self.jump_timer <= 0:
                self.state = "JUMPING"
                self.jump_timer = 0.5 # duree de saut en l'air
                self.set_sprites(self.sprite_jump)

        elif self.state == "JUMPING":
            self.jump_timer -= dt
            jump_duration = 0.5
            
            p = 1.0 - (max(0, self.jump_timer) / jump_duration)
            
            if p >= 1.0:
                # Fin du saut
                self.x = self.jump_target_x
                self.y = self.jump_target_y
                
                self.state = "LANDING"
                self.jump_timer = 0.5 # 0.5s de recuperation
                self.set_sprites(self.sprite_pre_jump)
            else:
                # Interpolation linéaire pour x et la base de y
                base_x = self.jump_start_x + (self.jump_target_x - self.jump_start_x) * p
                base_y = self.jump_start_y + (self.jump_target_y - self.jump_start_y) * p
                
                # effet parabolique avec un sinus
                jump_height = settings.tile_size * 1.5
                offset_y = math.sin(p * math.pi) * jump_height
                
                self.x = base_x
                self.y = base_y - offset_y 

            self.update_graphics()

        elif self.state == "LANDING":
            self.jump_timer -= dt
            if self.jump_timer <= 0:
                self.state = "NORMAL"
                self.set_sprites(self.sprite_normal)

    def try_hit_player(self, scene):
        if self.state == "NORMAL":
            super().try_hit_player(scene)

    def take_damage(self, scene, damage, source=None):
        # Insensible pendant le vol
        if self.state == "JUMPING":
            return
        super().take_damage(scene, damage, source)