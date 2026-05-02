# -*- coding: utf-8 -*-
"""
Ecran d'inventaire (Tab pour ouvrir/fermer).

Affiche une grille 5x6 = 30 slots.
  - Rangee 0 (en haut) : slots actifs HUD (visuellement distincte).
  - Rangees 1-4        : stockage etendu.

Les icones sont lues depuis sm.inventory au moment du show().
Le drag-and-drop est prevu : les methodes _on_slot_drag et _on_slot_drop
sont des hooks vides a implementer ulterieurement.

Navigation : Tab ou Echap pour fermer.
"""

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QRectF

from game.screens.base_screen import BaseScreen
from game.config import GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE, Z_SCREEN, KEYS
from game.fonts import get_font0

_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

# --- geometrie du panneau ---
_SLOT_SIZE    = 52
_SLOT_SPACING = 8
_COLS         = 6
_ROWS         = 5
_HUD_EXTRA_GAP = 14   # espace supplementaire entre rangee HUD et le reste

_GRID_W = _COLS * (_SLOT_SIZE + _SLOT_SPACING) - _SLOT_SPACING  # 352
_GRID_H = (_ROWS * (_SLOT_SIZE + _SLOT_SPACING) - _SLOT_SPACING
           + _HUD_EXTRA_GAP)                                      # 306

_PANEL_PAD = 22
_TITLE_H   = 50
_HINT_H    = 28
_PANEL_W   = _GRID_W + 2 * _PANEL_PAD         # 396
_PANEL_H   = _TITLE_H + _GRID_H + _HINT_H + 2 * _PANEL_PAD  # 428

_PANEL_X   = (_SCENE_W - _PANEL_W) // 2
_PANEL_Y   = (_SCENE_H - _PANEL_H) // 2

_GRID_X    = _PANEL_X + _PANEL_PAD
_GRID_Y    = _PANEL_Y + _PANEL_PAD + _TITLE_H

# --- couleurs ---
_C_OVERLAY    = QColor(0,  0,  0,  170)
_C_PANEL_BG   = QColor(18, 18, 36, 250)
_C_PANEL_BRD  = QColor(70, 70, 110)
_C_SLOT_HUD   = QColor(40, 40, 80,  230)
_C_SLOT_BRD_H = QColor(100, 100, 180)
_C_SLOT_STD   = QColor(28, 28, 55,  230)
_C_SLOT_BRD_S = QColor(60,  60,  100)
_C_TITLE      = QColor(180, 180, 255)
_C_HINT       = QColor(90,  90,  130)


def _slot_row_y(row):
    """Calcule la position Y du haut d'une rangee (avec gap apres rangee 0)."""
    if row == 0:
        return _GRID_Y
    return _GRID_Y + (_SLOT_SIZE + _SLOT_SPACING) + _HUD_EXTRA_GAP + (row - 1) * (_SLOT_SIZE + _SLOT_SPACING)


class InventoryScreen(BaseScreen):
    """Ecran d'inventaire avec grille 5x6 de slots."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._slot_bg_rects = []    # QGraphicsRectItem de fond pour chaque slot
        self._icon_items    = [None] * 30   # QGraphicsPixmapItem d'icone par slot
        self._slot_positions = []   # (x, y) de chaque slot (calcule en _build)

    # ------------------------------------------------------------------
    # cycle de vie (surcharge pour gerer les icones hors self._items)
    # ------------------------------------------------------------------

    def show(self, scene):
        super().show(scene)
        self._refresh_icons(scene)

    def hide(self):
        for icon in self._icon_items:
            if icon is not None:
                s = icon.scene()
                if s:
                    s.removeItem(icon)
        super().hide()

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def _build(self):
        self._build_overlay()
        self._build_panel()
        self._build_title()
        self._build_slots()
        self._build_hint()

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
        overlay.setBrush(QBrush(_C_OVERLAY))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_panel(self):
        panel = QGraphicsRectItem(_PANEL_X, _PANEL_Y, _PANEL_W, _PANEL_H)
        panel.setBrush(QBrush(_C_PANEL_BG))
        panel.setPen(QPen(_C_PANEL_BRD, 2))
        panel.setZValue(Z_SCREEN + 1)
        self._items.append(panel)

    def _build_title(self):
        title = QGraphicsTextItem("Inventaire")
        title.setFont(get_font0(size=38))
        title.setDefaultTextColor(_C_TITLE)
        title.setZValue(Z_SCREEN + 2)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, _PANEL_Y + _PANEL_PAD)
        self._items.append(title)

    def _build_slots(self):
        self._slot_bg_rects = []
        self._slot_positions = []
        for i in range(30):
            col = i % _COLS
            row = i // _COLS
            x = _GRID_X + col * (_SLOT_SIZE + _SLOT_SPACING)
            y = _slot_row_y(row)
            self._slot_positions.append((x, y))

            is_hud = (row == 0)
            bg_color  = _C_SLOT_HUD  if is_hud else _C_SLOT_STD
            brd_color = _C_SLOT_BRD_H if is_hud else _C_SLOT_BRD_S

            rect = QGraphicsRectItem(x, y, _SLOT_SIZE, _SLOT_SIZE)
            rect.setBrush(QBrush(bg_color))
            rect.setPen(QPen(brd_color, 1))
            rect.setZValue(Z_SCREEN + 2)
            self._items.append(rect)
            self._slot_bg_rects.append(rect)

    def _build_hint(self):
        key1 = QKeySequence(KEYS["LEAVE"]).toString()
        key2 = QKeySequence(KEYS["INVENTORY"]).toString()
        key3 = QKeySequence(KEYS["PAUSE"]).toString()
        hint = QGraphicsTextItem(f"{key1} / {key2} / {key3} pour fermer")
        hint.setFont(get_font0(size=14))
        hint.setDefaultTextColor(_C_HINT)
        hint.setZValue(Z_SCREEN + 2)
        hw = hint.boundingRect().width()
        hint.setPos((_SCENE_W - hw) / 2, _PANEL_Y + _PANEL_H - _PANEL_PAD - _HINT_H + 6)
        self._items.append(hint)

    # ------------------------------------------------------------------
    # mise a jour des icones
    # ------------------------------------------------------------------

    def _refresh_icons(self, scene):
        """Relit l'inventaire et (re)affiche les icones dans les slots."""
        # suppression des anciennes icones
        for i, icon in enumerate(self._icon_items):
            if icon is not None:
                s = icon.scene()
                if s:
                    s.removeItem(icon)
                self._icon_items[i] = None

        inventory = getattr(self.screen_manager, 'inventory', None)
        if inventory is None:
            return

        for i in range(30):
            slot = inventory.get_slot(i)
            if slot is None or slot.icon is None:
                continue
            x, y = self._slot_positions[i]
            icon_item = QGraphicsPixmapItem(
                slot.icon.scaled(
                    _SLOT_SIZE, _SLOT_SIZE,
                    Qt.KeepAspectRatio, Qt.FastTransformation
                )
            )
            icon_item.setPos(x, y)
            icon_item.setZValue(Z_SCREEN + 3)
            scene.addItem(icon_item)
            self._icon_items[i] = icon_item

    # ------------------------------------------------------------------
    # evenements
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key in (KEYS["LEAVE"], KEYS["INVENTORY"]):
            self.screen_manager.close_inventory()

    def mouse_press(self, scene_pos):
        for i, (x, y) in enumerate(self._slot_positions):
            if QRectF(x, y, _SLOT_SIZE, _SLOT_SIZE).contains(scene_pos):
                self._on_slot_click(i, scene_pos)
                return

    # ------------------------------------------------------------------
    # hooks drag-and-drop (a implementer ulterieurement)
    # ------------------------------------------------------------------

    def _on_slot_click(self, slot_index, scene_pos):
        """Appele lors d'un clic sur un slot. Point d'entree futur pour le drag-and-drop."""
        pass

    def _on_slot_drag(self, from_index):
        """Demarre un drag depuis un slot. A implementer."""
        pass

    def _on_slot_drop(self, from_index, to_index):
        """Depose un item sur un slot. A implementer."""
        pass
