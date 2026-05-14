# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt
from abc import abstractmethod
from game.config import DEBUG, TILE_SIZE, BASE_TILE_SIZE


class Interactable(QGraphicsPixmapItem):
    """
    Classe mere de tous les objets interactifs du jeu.

    Exemples :
        - SavePoint
        - NPC
        - Coffre
        - Panneau
    """

    def __init__(self, scale=1):
        super().__init__()

        self.setZValue(20)
        self.scale = scale
        self.tile_size = BASE_TILE_SIZE * scale
        
        # POSITION 
        self.x = 0
        self.y = 0
        
        # PROPRIETES
        
         # optionnel
        self.interactable_id = None
        # Type logique ("savepoint", "npc",...)
        self.type = "interactable"
        # par defaut pas de collision, exception pour coffre et panneau
        self.collision = 0

        # HITBOX D'INTERACTION
        self.hitbox_offset_x = 0
        self.hitbox_offset_y = 0
        self.hitbox_width = self.tile_size
        self.hitbox_height = self.tile_size
        
        if DEBUG:
            self.debug_rect = QGraphicsRectItem(self)
            self.debug_rect.setPen(QPen(QColor("yellow"), 1))
            self.debug_rect.setZValue(999)
            
    def get_hitbox(self, x=None, y=None):
        """
        renvoie les coordonnees de la hitbox d'interaction
        """
        if x is None: x = self.x
        if y is None: y = self.y

        return (
            x + self.hitbox_offset_x * self.tile_size,
            y + self.hitbox_offset_y * self.tile_size,
            self.hitbox_width,
            self.hitbox_height
        )
    
    def set_grid_position(self, x, y, tile_size, hud_offset=0):
        """
        positionne l'objet sur la grille et met a jour le visuel
        """
        self.x = x * tile_size
        self.y = (y + hud_offset) * tile_size
        self.update_graphics()
        
    def update_graphics(self):
        self.setPos(self.x, self.y)

        if hasattr(self, "debug_rect"):
            hx, hy, hw, hh = self.get_hitbox()
            self.debug_rect.setRect(
                hx - self.x,
                hy - self.y,
                hw,
                hh
            )
            
    def distance_to(self, other):
        """
        Utilitaire optionnel pour interactions avancées.
        """
        return (self.pos() - other.pos()).manhattanLength()

    @abstractmethod
    def interact(self, scene, player=None):
        """
        appelee lorsque joueur interagit avec objet
        """
        pass

    def update(self, dt):
        pass
    
