# -*- coding: utf-8 -*-
"""
Ecran de game over.

Options proposees :
  - Recommencer           → nouvelle partie depuis le debut
  - Retour au menu        → retour a l'ecran titre
  - Point de sauvegarde   → grise (sauvegarde non implantee)
  - Quitter               → ferme l'application

Navigation : fleches haut/bas + Entree, ou clic souris.
"""

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt, QRectF

from game.screens.base_screen import BaseScreen
from game.config import (
    GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE,
    Z_SCREEN,
)
from game.fonts import get_font0

_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

# --- geometrie ---
_BTN_W       = 340
_BTN_H       = 52
_BTN_SPACING = 16
_BTN_X       = (_SCENE_W - _BTN_W) // 2
_FIRST_BTN_Y = int(_SCENE_H * 0.52)

# --- couleurs ---
_C_BG_NORMAL   = QColor(30,  15,  15,  185)
_C_BG_SELECTED = QColor(110,  20,  20,  225)
_C_TXT_NORMAL  = QColor(200, 200, 200)
_C_TXT_SELECT  = QColor(255,  80,  80)
_C_TXT_DISABLED= QColor(70,   70,  70)


class GameOverScreen(BaseScreen):
    """Ecran affiche apres la mort du joueur."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self._menu = [
            {"label": "Recommencer",          "action": "restart",   "enabled": True},
            {"label": "Retour au menu",        "action": "menu",      "enabled": True},
            {"label": "Point de sauvegarde",   "action": "load_save", "enabled": False},
            {"label": "Quitter",               "action": "quit",      "enabled": True},
        ]
        self._selected = 0
        self._btns     = []

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def _build(self):
        self._build_overlay()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
        overlay.setBrush(QBrush(QColor(0, 0, 0, 210)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_title(self):
        title = QGraphicsTextItem("Game Over")
        title.setFont(get_font0(size=56))
        title.setDefaultTextColor(QColor(200, 30, 30))
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, int(_SCENE_H * 0.26))
        self._items.append(title)

    def _build_menu(self):
        self._btns = []
        for i, entry in enumerate(self._menu):
            y = _FIRST_BTN_Y + i * (_BTN_H + _BTN_SPACING)

            rect = QGraphicsRectItem(_BTN_X, y, _BTN_W, _BTN_H)
            rect.setBrush(QBrush(_C_BG_NORMAL))
            rect.setPen(QPen(Qt.NoPen))
            rect.setZValue(Z_SCREEN + 1)

            text = QGraphicsTextItem(entry["label"])
            text.setFont(get_font0(size=24))
            text.setZValue(Z_SCREEN + 2)

            color = _C_TXT_NORMAL if entry["enabled"] else _C_TXT_DISABLED
            text.setDefaultTextColor(color)

            tw = text.boundingRect().width()
            th = text.boundingRect().height()
            text.setPos(_BTN_X + (_BTN_W - tw) / 2, y + (_BTN_H - th) / 2)

            self._items.extend([rect, text])
            self._btns.append({"rect": rect, "text": text, "y": y})

    def _refresh_highlight(self):
        for i, btn in enumerate(self._btns):
            if not self._menu[i]["enabled"]:
                continue
            if i == self._selected:
                btn["rect"].setBrush(QBrush(_C_BG_SELECTED))
                btn["text"].setDefaultTextColor(_C_TXT_SELECT)
            else:
                btn["rect"].setBrush(QBrush(_C_BG_NORMAL))
                btn["text"].setDefaultTextColor(_C_TXT_NORMAL)

    # ------------------------------------------------------------------
    # navigation clavier
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key in (Qt.Key_Down, Qt.Key_Right):
            self._move(+1)
        elif key in (Qt.Key_Up, Qt.Key_Left):
            self._move(-1)
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._activate()

    def _move(self, direction):
        n     = len(self._menu)
        index = self._selected
        for _ in range(n):
            index = (index + direction) % n
            if self._menu[index]["enabled"]:
                break
        self._selected = index
        self._refresh_highlight()

    def _activate(self):
        self._dispatch(self._menu[self._selected]["action"])

    # ------------------------------------------------------------------
    # navigation souris
    # ------------------------------------------------------------------

    def mouse_press(self, scene_pos):
        for i, btn in enumerate(self._btns):
            if not self._menu[i]["enabled"]:
                continue
            if QRectF(_BTN_X, btn["y"], _BTN_W, _BTN_H).contains(scene_pos):
                self._selected = i
                self._refresh_highlight()
                self._dispatch(self._menu[i]["action"])
                return

    # ------------------------------------------------------------------
    # dispatch des actions
    # ------------------------------------------------------------------

    def _dispatch(self, action):
        sm = self.screen_manager
        if action == "restart":
            sm.start_new_game()
        elif action == "menu":
            sm.go_to_title()
        elif action == "load_save":
            pass   # non implante
        elif action == "quit":
            sm.quit_game()
