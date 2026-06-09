# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QColor

from game.config import Z_SCREEN
from game.fonts import get_font0
from game.settings import settings

_C_NORMAL   = QColor(190, 190, 210)
_C_SELECTED = QColor(255, 215, 0)


class OptionRow:
    """
    Ligne d'option pour ecran parametres.
    Affiche un label a gauche et une valeur cyclable < Valeur > a droite.
    """

    def __init__(self, label, options, x_label, x_value, y, value_width, z=Z_SCREEN + 2):
        """
        label       : texte du label ("Volume musique")
        options     : liste de tuples (nom_affiche, valeur_interne)
                      ex: [("Bas", 0.25), ("Moyen", 0.50), ("Élevé", 0.75)]
        x_label     : position X du label
        x_value     : position X de la zone de valeur
        y           : position Y de la ligne
        value_width : largeur de la zone de valeur (pour centrer le texte)
        """
        self.options     = options
        self.current     = 0
        self.x_value     = x_value
        self.value_width = value_width
        self.y           = y
        self.height      = settings.tile_size

        # --- label (cote gauche) ---
        self.label_item = QGraphicsTextItem(label)
        self.label_item.setFont(get_font0(size=5))
        self.label_item.setDefaultTextColor(_C_NORMAL)
        self.label_item.setZValue(z)
        lh = self.label_item.boundingRect().height()
        self.label_item.setPos(x_label, y + (settings.tile_size - lh) / 2)

        # --- valeur (cote droit) ---
        self.value_item = QGraphicsTextItem()
        self.value_item.setFont(get_font0(size=5))
        self.value_item.setDefaultTextColor(_C_NORMAL)
        self.value_item.setZValue(z)
        self._update_display()

    def _update_display(self):
        """Met a jour le texte affiche et le recentre."""
        name = self.options[self.current][0]
        self.value_item.setPlainText(f"<  {name}  >")
        tw = self.value_item.boundingRect().width()
        th = self.value_item.boundingRect().height()
        self.value_item.setPos(
            self.x_value + (self.value_width - tw) / 2,
            self.y + (settings.tile_size - th) / 2,
        )

    def cycle(self, direction):
        """Passe a l'option suivante (+1) ou precedente (-1)."""
        self.current = (self.current + direction) % len(self.options)
        self._update_display()

    def get_value(self):
        """Renvoie la valeur interne de l'option selectionnee."""
        return self.options[self.current][1]

    def set_value(self, value):
        """Selectionne l'option dont la valeur est la plus proche."""
        best = 0
        best_diff = float("inf")
        for i, (_, v) in enumerate(self.options):
            if v == value:
                best = i
                break
            if isinstance(v, (int, float)) and isinstance(value, (int, float)):
                diff = abs(v - value)
                if diff < best_diff:
                    best = i
                    best_diff = diff
        self.current = best
        self._update_display()

    def set_selected(self, selected):
        """Change l'apparence selon que la ligne est selectionnee ou non."""
        color = _C_SELECTED if selected else _C_NORMAL
        self.label_item.setDefaultTextColor(color)
        self.value_item.setDefaultTextColor(color)

    def get_items(self):
        """Renvoie les QGraphicsItems a ajouter a la scene."""
        return [self.label_item, self.value_item]
