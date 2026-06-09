# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy

from game.settings import settings
from game.config import FPS
import random


class Tralalero(Enemy):
    """Ennemi rapide ecoutant et reagissant avec un cri (Tralala)."""
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = self.speed*1.2
        self._pv_max = 5
        self.pv_main = self._pv_max
        
        self.aggro_range = settings.tile_size * 6
        
        self.damage = 1.5
        self.give_stun = 0
        
        self.loot = [
            ("bombe",0.4),
            ("mana",0.25)
        ]

        # --- SPRITE UNIQUE (meme pour toutes directions) ---
        sprite = QPixmap("assets/enemies/tralalero/tralalero.png").scaled(
            settings.tile_size*2,
            settings.tile_size,
            transformMode=Qt.FastTransformation
        )

        self.sprites = {
            "down": sprite,
            "up": sprite,
            "left": sprite,
            "right": sprite
        }
        
        self.use_pathfinding = False
        self.can_go_on_water = True
        self.hitbox_width = settings.tile_size * 2
        
        self.sfx_timer = random.uniform(0.7, 2.0)
        self.sfx_timer = 0
        

    def update(self, dt, scene):
        """Met a jour la logique de deplacement et emet un son periodiquement."""
        self.sfx_timer -= dt
        
        if self.sfx_timer < 0:
            scene.sfx_manager.play("snd_tralala")
            self.sfx_timer = random.uniform(3.0, 6.0)

            
        super().update(dt,scene)