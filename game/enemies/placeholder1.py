# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy


class Placeholder1(Enemy):
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = self.speed/3
        self._pv_max = 2
        self.pv_main = self._pv_max
        
        self.aggro_range = self.tile_size * 10
        
        self.damage = 1
        self.give_stun = 0
        
        self.loot = [
            ("pomme",0.5)
        ]

        # --- SPRITE UNIQUE (même pour toutes directions) ---
        sprite = QPixmap("assets/placeholder1.png").scaled(
            self.tile_size,
            self.tile_size,
            transformMode=Qt.FastTransformation
        )

        self.sprites = {
            "down": sprite,
            "up": sprite,
            "left": sprite,
            "right": sprite
        }

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
    