# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

import math
import random
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy
from game.settings import settings
from game.config import BASE_TILE_SIZE

class Fly(Enemy):
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS DE BASE ---
        self._pv_max = 1
        self.pv_main = self._pv_max
        self.speed = settings.base_speed * 1.6
        
        # --- HITBOX ---
        self.hitbox_offset_x = 7 / BASE_TILE_SIZE
        self.hitbox_offset_y = 8 / BASE_TILE_SIZE
        self.hitbox_width = settings.tile_size * 0.125
        self.hitbox_height = settings.tile_size * 0.125
        
        self.aggro_range = settings.tile_size * 11
        self.damage = 0.5
        self.give_stun = 0
        
        self.loot = []
        self.can_go_on_water = True
        
        # --- AUDIO ---
        self.death_cry = "snd_mouche_death"
        self.sfx_timer = random.uniform(0.5, 2.0)

        # --- SPRITE UNIQUE ---
        sprite = QPixmap("assets/enemies/fly/fly.png").scaled(
            int(settings.tile_size),
            int(settings.tile_size),
            transformMode=Qt.FastTransformation
        )

        self.sprites = {
            "down": sprite,
            "up": sprite,
            "left": sprite,
            "right": sprite
        }

        # --- PARAMÈTRES IA (MOUVEMENT VOLANT) ---
        self.use_pathfinding = False
        
        self.ai_state = "circling" # Deux états : "circling" (tourne) et "dashing" (fonce)
        self.orbit_angle = random.uniform(0, 2 * math.pi)
        self._base_orbit_radius = random.uniform(3, 4.5) * settings.tile_size
        self.orbit_radius = self._base_orbit_radius
        self.orbit_speed = 4.0 # Vitesse de rotation en radians
        
        self.dash_cooldown = random.uniform(5.0, 10.0)
        self.dash_duration = 0.0

    def update(self, dt, scene):
        if self.kb_active:
            self.apply_knockback(dt, scene)
            self.update_graphics()
            self.update_damage_state(dt)
            return
        
        if self.is_stunned:
            self.apply_stun_wiggle(dt, scene)
            self.update_graphics()
            self.update_damage_state(dt)
            self.update_stun_animation(dt)
            return

        if not self.target:
            return

        dx_target = self.target.x - self.x
        dy_target = self.target.y - self.y
        dist_to_player = math.hypot(dx_target, dy_target)

        if dist_to_player > self.aggro_range:
            self.wander(dt, scene)
            self.update_graphics()
            self.update_damage_state(dt)
            return

        # --- LECTURE DES EFFETS SONORES (SFX) ---
        self.sfx_timer -= dt
        if self.sfx_timer <= 0:
            sfx_index = random.randint(1, 14)
            sfx_name = f"snd_mouche{sfx_index}"
            
            if hasattr(scene, "sfx_manager"):
                dx_from_player = self.x - self.target.x
                
                max_dist = 4 * settings.tile_size
                
                pan = max(-1.0, min(1.0, dx_from_player / max_dist))
                
                scene.sfx_manager.play(sfx_name, pan=pan)
            
            self.sfx_timer = random.uniform(0.7, 2.0)


        # --- MACHINE A ETATS DE L'IA ---
        dx, dy = 0, 0

        if self.ai_state == "circling":
            self.dash_cooldown -= dt
            
            if self.dash_cooldown <= 0:
                # Transition vers l'attaque
                self.ai_state = "dashing"
                self.dash_duration = 0.8
                self.speed = settings.base_speed * 3
            else:
                # Logique d'orbite autour du joueur
                self.orbit_angle += self.orbit_speed * dt
                
                # Coordonnées du point cible sur le cercle d'orbite
                target_x = self.target.x + math.cos(self.orbit_angle) * self.orbit_radius
                target_y = self.target.y + math.sin(self.orbit_angle) * self.orbit_radius
                
                dx = target_x - self.x
                dy = target_y - self.y

        elif self.ai_state == "dashing":
            self.dash_duration -= dt
            
            if self.dash_duration <= 0:
                # Retourne au comportement "circling"
                self.ai_state = "circling"
                self.dash_cooldown = random.uniform(5.0, 10.0)
                self.orbit_radius = self._base_orbit_radius
                self.speed = settings.base_speed * 1.6 # Restaure la vitesse standard
            else:
                # Fonce droit sur le joueur
                dx = self.target.x - self.x
                dy = self.target.y - self.y

        # --- NORMALISATION ET MOUVEMENT ---
        dist_move = math.hypot(dx, dy)
        if dist_move > 0:
            dx /= dist_move
            dy /= dist_move

        if dx != 0 or dy != 0:
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

        self.move(dx, dy, dt, scene)
        self.update_graphics()
        self.update_stun_animation(dt)
        self.update_damage_state(dt)
        
        # Test de collision
        self.try_hit_player(scene)
    
    def die(self):
        scene = self.scene()
        scene.sfx_manager.stop_all_except([self.death_cry,"snd_sad"])
        super().die()