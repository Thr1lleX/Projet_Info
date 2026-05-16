# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QRectF

from game.config import Z_SCREEN
from game.fonts import get_font0
from game.settings import settings

# --- Chemins des 3 sprites de bouton ---
_PATH_NORMAL   = "assets/hud/hud_select1.png"
_PATH_SELECTED = "assets/hud/hud_select2.png"
_PATH_PRESSED  = "assets/hud/hud_select3.png"

# --- Dimensions en tiles ---
_BTN_WIDTH_TILES  = 7
_BTN_HEIGHT_TILES = 1

# --- Couleurs du texte selon l'état ---
_TXT_NORMAL   = QColor(200, 200, 200)
_TXT_SELECTED = QColor(255, 215, 0)
_TXT_PRESSED  = QColor(255, 255, 255)
_TXT_DISABLED = QColor(80, 80, 80)

class SpriteButton:
    """
    Bouton de menu avec sprite hud_select.
    Gere 3 etats visuels : normal, selected, pressed.
    """

    def __init__(self, label, x, y, z=Z_SCREEN + 1, enabled=True):
        # --- Dimensions finales en pixels (scalees avec tile_size) ---
        self.width  = _BTN_WIDTH_TILES * settings.tile_size
        self.height = _BTN_HEIGHT_TILES * settings.tile_size
        self.x = x
        self.y = y
        self.enabled = enabled

        # --- Charger et scaler les 3 sprites ---
        self._pixmaps = {
            "normal":   self._load_scaled(_PATH_NORMAL),
            "selected": self._load_scaled(_PATH_SELECTED),
            "pressed":  self._load_scaled(_PATH_PRESSED),
        }

        # --- Creer l'item image (le fond du bouton) ---
        self.sprite = QGraphicsPixmapItem(self._pixmaps["normal"])
        self.sprite.setPos(x, y)
        self.sprite.setZValue(z)

        # --- Creer l'item texte (par-dessus le sprite) ---
        self.text = QGraphicsTextItem(label)
        self.text.setFont(get_font0(size=6))
        self.text.setZValue(z + 1)
        self._center_text()

        # --- Etat initial ---
        self.set_state("normal")

    def _load_scaled(self, path):
        """Charge un PNG et le scale a la taille finale du bouton."""
        pix = QPixmap(path)
        return pix.scaled(
            self.width, self.height,
            Qt.IgnoreAspectRatio, 
            Qt.FastTransformation # pas de flou de lissage
        )

    def _center_text(self):
        """Centre le texte horizontalement et verticalement dans le bouton."""
        tw = self.text.boundingRect().width()
        th = self.text.boundingRect().height()
        self.text.setPos(
            self.x + (self.width - tw) / 2,
            self.y + (self.height - th) / 2
        )

    def set_state(self, state):
        """Change l'etat visuel : 'normal', 'selected', ou 'pressed'."""
        self.sprite.setPixmap(self._pixmaps[state])

        if not self.enabled:
            self.text.setDefaultTextColor(_TXT_DISABLED)
        elif state == "selected":
            self.text.setDefaultTextColor(_TXT_SELECTED)
        elif state == "pressed":
            self.text.setDefaultTextColor(_TXT_PRESSED)
        else:
            self.text.setDefaultTextColor(_TXT_NORMAL)

    def contains(self, scene_pos):
        """Teste si un point (clic souris) est dans la zone du bouton."""
        return QRectF(self.x, self.y, self.width, self.height).contains(scene_pos)

    def get_items(self):
        """Renvoie la liste des QGraphicsItems a ajouter a la scene."""
        return [self.sprite, self.text]

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    btn = SpriteButton("Test", 100, 100)
    print(f"Bouton: {btn.width}x{btn.height} px")
    print(f"Items: {len(btn.get_items())}")
    print("OK!")

    
