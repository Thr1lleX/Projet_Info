# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy

from game.settings import settings


class Crouby(Enemy):
    """Ennemi lent avec beaucoup de points de vie (tank)."""
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = self.speed/2.5
        self._pv_max = 6
        self.pv_main = self._pv_max
        
        self.aggro_range = settings.tile_size * 9
        
        self.damage = 2
        self.give_stun = 0
        
        self.loot = [
            ("pomme",0.25),
            ("mana",0.12)
        ]
        

        # --- SPRITE UNIQUE (même pour toutes directions) ---
        sprite = QPixmap("assets/enemies/crouby/crouby.png").scaled(
            settings.tile_size,
            settings.tile_size,
            transformMode=Qt.FastTransformation
        )

        self.sprites = {
            "down": sprite,
            "up": sprite,
            "left": sprite,
            "right": sprite
        }