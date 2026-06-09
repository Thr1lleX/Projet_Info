# -*- coding: utf-8 -*-
"""Gere l'animation d'effet 'poof' (apparition/disparition)."""
from PyQt5.QtWidgets import QGraphicsPixmapItem
from game.animspr import load_animation_sequence
from game.settings import settings
from game.config import HUD_HEIGHT

class PoofEffect(QGraphicsPixmapItem):
    def __init__(self, x, y):
        """Initialise l'animation visuelle a la position donnee."""
        super().__init__()
        self.frames = load_animation_sequence("assets/effects/poof_tile", (1, 1))
        self.setPixmap(self.frames[0])
            
        self.current_frame = 0
        self.timer = 0
        self.frame_duration = 0.08
        self.setPos(x * settings.tile_size, (y + HUD_HEIGHT) * settings.tile_size)
        self.setZValue(10)

    def update(self, dt):
        """Met a jour les frames de l'animation. Retourne True si terminee."""
        if not self.frames: return True
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.setPixmap(self.frames[self.current_frame])
                return False
            return True
        return False