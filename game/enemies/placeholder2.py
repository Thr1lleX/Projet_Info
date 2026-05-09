# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy
from game.rick import RickWindow

import random

class Placeholder2(Enemy):
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = self.speed / 20
        self._pv_max = 10
        self.pv_main = self._pv_max
        self.aggro_range = self.tile_size * 10
        
        self.invuln_duration = 5
        self.effect_immunity_duration = 1.5
        
        # -- Parametres d'attaque ---
        self.damage = 2
        self.give_stun = 10

        # --- HITBOX ---
        self.hitbox_offset_x = 0
        self.hitbox_offset_y = 0
        self.hitbox_width = self.tile_size * 2
        self.hitbox_height = self.tile_size * 2
        
        self.knockback = 7
        self.duree_knockback = 1.5

        # --- SPRITE UNIQUE (même pour toutes directions) ---
        sprite = QPixmap("assets/placeholder2.png").scaled(
            self.tile_size * 2,
            self.tile_size * 2,
            transformMode=Qt.FastTransformation
        )

        self.sprites = {
            "down": sprite,
            "up": sprite,
            "left": sprite,
            "right": sprite
        }

    def die(self):
        if random.randint(0, 10) == 0:
            self.rick()
        super().die()

    def rick(self):
        self.rick_window = RickWindow(self.scene().music_manager)
        self.rick_window.show()

    # def update(self, dt, scene):
    #     if not self.target:
    #         return

    #     dx = self.target.x - self.x
    #     dy = self.target.y - self.y

    #     dist = (dx**2 + dy**2) ** 0.5

    #     if dist > 0:
    #         dx /= dist
    #         dy /= dist

    #         # direction (optionnel mais propre)
    #         if abs(dx) > abs(dy):
    #             self.direction = "right" if dx > 0 else "left"
    #         else:
    #             self.direction = "down" if dy > 0 else "up"

    #     self.move(dx, dy, dt, scene)
    #     self.update_graphics()
    #     self.update_damage_state(dt)