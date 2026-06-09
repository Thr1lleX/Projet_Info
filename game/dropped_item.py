# Auteur : essentiellement Ryan
"""Representation graphique d'un objet tombe au sol."""

from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.item_registry import get_item_data
from game.settings import settings

class DroppedItem(QGraphicsPixmapItem):
    """Element visuel et physique d'un objet present dans la scene."""
    def __init__(self, item_id, x, y):
        super().__init__()
        self.item_id = item_id
        
        # charger et scaler le sprite
        data = get_item_data(item_id)
        pix = QPixmap(data["icon_path"])
        size = int(settings.tile_size * 0.75)
        self.setPixmap(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation))

        # position dans la scene
        self.x = x
        self.y = y
        self.setPos(x, y)
        self.setZValue(50)

        self._size = size

    
    def get_rect(self):
        """Renvoie (x, y, w, h) pour la detection de collision."""
        return (self.x, self.y, self._size, self._size)
