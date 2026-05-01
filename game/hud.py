# -*- coding: utf-8 -*-
"""
Gestion du HUD (barre d'interface du haut).
Affiche les points de vie (coeurs) et les slots d'items.

Pour ajouter un element au HUD a l'avenir :
  1. Creer les QGraphicsItems dans une methode _build_xxx()
  2. Les ajouter a self._items via self._items.extend(...)
  3. Appeler _build_xxx() depuis __init__
"""

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt

from game.config import (
    TILE_SIZE, GRID_WIDTH, HUD_HEIGHT,
    HUD_ITEM_SLOTS,
    HUD_HEART_FULL_PATH, HUD_HEART_EMPTY_PATH, HUD_ITEM_SLOT_PATH,
    Z_HUD,
)

# --- constantes visuelles du HUD (ajustables sans toucher a la logique) ---
HEART_SIZE        = int(TILE_SIZE * 0.90)   # 38px a SCALE=4
SLOT_SIZE         = int(TILE_SIZE * 0.90)
SPACING           = 6                        # pixels entre chaque icone
HEART_MARGIN_LEFT = 16
SLOT_MARGIN_RIGHT = 16

_HUD_W = GRID_WIDTH * TILE_SIZE             # 1024px
_HUD_H = HUD_HEIGHT * TILE_SIZE             # 128px


class HUD:
    """
    Gere tous les elements visuels de la barre du haut.
    Instancie les QGraphicsItems et les ajoute directement a la scene.
    Les items sont recuperables via get_items() pour les rendre persistants.
    """

    def __init__(self, scene):
        self._items = []          # tous les QGraphicsItems geres par ce HUD
        self._heart_pairs = []    # liste de (full_item, empty_item) par slot de coeur
        self._slot_data   = []    # liste de dict {bg, icon, x, y} par slot d'item

        self._current_pv     = -1
        self._current_pv_max = -1

        self._build_background(scene)
        self._build_hearts(scene, pv_max=5)
        self._build_slots(scene)

    # ------------------------------------------------------------------
    # construction initiale
    # ------------------------------------------------------------------

    def _build_background(self, scene):
        bg = QGraphicsRectItem(0, 0, _HUD_W, _HUD_H)
        bg.setBrush(QBrush(QColor(0, 0, 0)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_HUD)
        scene.addItem(bg)
        self._items.append(bg)

    def _build_hearts(self, scene, pv_max):
        """Cree les paires d'icones (plein / vide) pour chaque slot de vie."""
        cy = (_HUD_H - HEART_SIZE) // 2

        for i in range(pv_max):
            x = HEART_MARGIN_LEFT + i * (HEART_SIZE + SPACING)

            full_item  = self._make_heart_item(x, cy, full=True)
            empty_item = self._make_heart_item(x, cy, full=False)

            for item in (full_item, empty_item):
                item.setZValue(Z_HUD + 1)
                scene.addItem(item)
                self._items.append(item)

            self._heart_pairs.append((full_item, empty_item))

        self._apply_heart_display(pv_max, pv_max)
        self._current_pv     = pv_max
        self._current_pv_max = pv_max

    def _make_heart_item(self, x, y, full):
        """
        Retourne un QGraphicsItem representant un coeur.
        Utilise le sprite si disponible, sinon un rectangle de couleur en placeholder.
        Sprites attendus : assets/hud/heart_full.png et assets/hud/heart_empty.png
        """
        path = HUD_HEART_FULL_PATH if full else HUD_HEART_EMPTY_PATH
        pix  = QPixmap(path)

        if not pix.isNull():
            item = QGraphicsPixmapItem(
                pix.scaled(HEART_SIZE, HEART_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
        else:
            item = QGraphicsRectItem(0, 0, HEART_SIZE, HEART_SIZE)
            item.setBrush(QBrush(QColor(210, 30, 30) if full else QColor(55, 10, 10)))
            item.setPen(QPen(Qt.NoPen))

        item.setPos(x, y)
        return item

    def _build_slots(self, scene):
        """Cree les fonds de slots d'items (vides par defaut)."""
        cy = (_HUD_H - SLOT_SIZE) // 2
        total_w = HUD_ITEM_SLOTS * (SLOT_SIZE + SPACING) - SPACING
        x_start = _HUD_W - SLOT_MARGIN_RIGHT - total_w

        for i in range(HUD_ITEM_SLOTS):
            x  = x_start + i * (SLOT_SIZE + SPACING)
            bg = self._make_slot_bg(x, cy)
            bg.setZValue(Z_HUD + 1)
            scene.addItem(bg)
            self._items.append(bg)
            self._slot_data.append({"bg": bg, "icon": None, "x": x, "y": cy})

    def _make_slot_bg(self, x, y):
        """
        Retourne le fond d'un slot d'item.
        Utilise le sprite si disponible, sinon un rectangle gris en placeholder.
        Sprite attendu : assets/hud/item_slot.png
        """
        pix = QPixmap(HUD_ITEM_SLOT_PATH)
        if not pix.isNull():
            item = QGraphicsPixmapItem(
                pix.scaled(SLOT_SIZE, SLOT_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
        else:
            item = QGraphicsRectItem(0, 0, SLOT_SIZE, SLOT_SIZE)
            item.setBrush(QBrush(QColor(35, 35, 35)))
            item.setPen(QPen(QColor(75, 75, 75), 2))

        item.setPos(x, y)
        return item

    # ------------------------------------------------------------------
    # mise a jour
    # ------------------------------------------------------------------

    def update_hearts(self, pv, pv_max):
        """
        Met a jour l'affichage des coeurs.
        Appele chaque frame depuis game_loop ; ne fait rien si les PV n'ont pas change.
        """
        if pv == self._current_pv and pv_max == self._current_pv_max:
            return
        self._current_pv     = pv
        self._current_pv_max = pv_max
        self._apply_heart_display(pv, pv_max)

    def _apply_heart_display(self, pv, pv_max):
        for i, (full_item, empty_item) in enumerate(self._heart_pairs):
            if i < pv:
                full_item.show()
                empty_item.hide()
            else:
                full_item.hide()
                empty_item.show()

    def update_item(self, slot_index, pixmap):
        """
        Place ou retire une icone dans un slot d'item (usage futur).

        slot_index : entier 0-based (0 a HUD_ITEM_SLOTS-1)
        pixmap     : QPixmap a afficher, ou None pour vider le slot
        """
        if not (0 <= slot_index < len(self._slot_data)):
            return

        slot = self._slot_data[slot_index]

        # suppression de l'icone precedente
        if slot["icon"] is not None:
            s = slot["icon"].scene()
            if s:
                s.removeItem(slot["icon"])
            slot["icon"] = None

        if pixmap is None:
            return

        icon = QGraphicsPixmapItem(
            pixmap.scaled(SLOT_SIZE, SLOT_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
        )
        icon.setPos(slot["x"], slot["y"])
        icon.setZValue(Z_HUD + 2)

        s = slot["bg"].scene()
        if s:
            s.addItem(icon)

        slot["icon"] = icon

    # ------------------------------------------------------------------
    # utilitaire
    # ------------------------------------------------------------------

    def get_items(self):
        """
        Retourne tous les QGraphicsItems du HUD.
        A passer a persistent_items de GameScene pour qu'ils survivent aux changements de salle.
        """
        return list(self._items)
