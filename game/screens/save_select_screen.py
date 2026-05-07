# -*- coding: utf-8 -*-
"""
Copier Coller du Title Screen


Ecran de sélection de sauvegarde.

Permet de charger :
    - Partie 1
    - Partie 2
    - Partie 3

Les slots inexistants sont grisés.

Navigation :
    - clavier
    - souris
"""

from PyQt5.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsPixmapItem,
    QGraphicsTextItem
)

from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPen,
    QPixmap
)

from PyQt5.QtCore import Qt, QRectF

from game.screens.base_screen import BaseScreen

from game.save_manager import SaveManager

from game.config import (
    GRID_WIDTH,
    GRID_HEIGHT,
    HUD_HEIGHT,
    TILE_SIZE,
    Z_SCREEN,
    TITLE_BG_PATH,
    KEYS
)

from game.fonts import get_font0


_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

# ---------------------------------------------------------
# BOUTONS
# ---------------------------------------------------------

_BTN_W = 300
_BTN_H = 52
_BTN_SPACING = 16
_BTN_X = (_SCENE_W - _BTN_W) // 2
_FIRST_BTN_Y = int(_SCENE_H * 0.50)

# ---------------------------------------------------------
# COULEURS
# ---------------------------------------------------------

_C_BG_NORMAL = QColor(20, 20, 20, 180)
_C_BG_SELECTED = QColor(90, 60, 10, 220)
_C_TXT_NORMAL = QColor(200, 200, 200)
_C_TXT_SELECT = QColor(255, 215, 0)
_C_TXT_DISABLED = QColor(80, 80, 80)


class SaveSelectScreen(BaseScreen):

    def __init__(self, screen_manager):

        super().__init__(screen_manager)

        self._menu = [

            {
                "label": "Partie 1",
                "action": "slot1",
                "enabled": SaveManager.save_exists(1)
            },

            {
                "label": "Partie 2",
                "action": "slot2",
                "enabled": SaveManager.save_exists(2)
            },

            {
                "label": "Partie 3",
                "action": "slot3",
                "enabled": SaveManager.save_exists(3)
            },

            {
                "label": "Retour",
                "action": "back",
                "enabled": True
            }
        ]

        self._selected = 0

        self._btns = []

        # sélectionne automatiquement
        # le premier slot valide
        self._select_first_enabled()

    # ---------------------------------------------------------
    # BUILD
    # ---------------------------------------------------------

    def _build(self):
        self._build_background()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_background(self):

        pix = QPixmap(TITLE_BG_PATH)
        if not pix.isNull():

            bg = QGraphicsPixmapItem(
                pix.scaled(
                    _SCENE_W,
                    _SCENE_H,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        else:
            bg = QGraphicsRectItem(
                0,
                0,
                _SCENE_W,
                _SCENE_H
            )
            bg.setBrush(QBrush(QColor(10, 10, 30)))
            bg.setPen(QPen(Qt.NoPen))

        bg.setZValue(Z_SCREEN)
        self._items.append(bg)

    def _build_title(self):
        title = QGraphicsTextItem("Choisir une sauvegarde")
        title.setFont(get_font0(size=48))
        title.setDefaultTextColor(QColor(255, 215, 0))
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos(
            (_SCENE_W - tw) / 2,
            int(_SCENE_H * 0.18)
        )

        self._items.append(title)

    def _build_menu(self):
        self._btns = []
        for i, entry in enumerate(self._menu):
            y = _FIRST_BTN_Y + i * (_BTN_H + _BTN_SPACING)

            rect = QGraphicsRectItem(
                _BTN_X,
                y,
                _BTN_W,
                _BTN_H
            )

            rect.setBrush(QBrush(_C_BG_NORMAL))
            rect.setPen(QPen(Qt.NoPen))
            rect.setZValue(Z_SCREEN + 1)
            text = QGraphicsTextItem(entry["label"])
            text.setFont(get_font0(size=24))
            text.setZValue(Z_SCREEN + 2)
            color = (
                _C_TXT_NORMAL
                if entry["enabled"]
                else _C_TXT_DISABLED
            )

            text.setDefaultTextColor(color)
            tw = text.boundingRect().width()
            th = text.boundingRect().height()
            text.setPos(
                _BTN_X + (_BTN_W - tw) / 2,
                y + (_BTN_H - th) / 2
            )

            self._items.extend([rect, text])
            self._btns.append({
                "rect": rect,
                "text": text,
                "y": y
            })

    # ---------------------------------------------------------
    # HIGHLIGHT
    # ---------------------------------------------------------

    def _refresh_highlight(self):
        for i, btn in enumerate(self._btns):
            if not self._menu[i]["enabled"]:
                continue
            if i == self._selected:
                btn["rect"].setBrush(
                    QBrush(_C_BG_SELECTED)
                )
                btn["text"].setDefaultTextColor(
                    _C_TXT_SELECT
                )
            else:
                btn["rect"].setBrush(
                    QBrush(_C_BG_NORMAL)
                )
                btn["text"].setDefaultTextColor(
                    _C_TXT_NORMAL
                )
    def _select_first_enabled(self):
        for i, entry in enumerate(self._menu):
            if entry["enabled"]:
                self._selected = i
                return

    # ---------------------------------------------------------
    # KEYBOARD
    # ---------------------------------------------------------

    def key_press(self, key):
        if key == KEYS["DOWN"]:
            self._move(+1)
        elif key == KEYS["UP"]:
            self._move(-1)
        elif key in (
            KEYS["ATTACK"],
            KEYS["INTERACT"],
            KEYS["CONFIRM"]
        ):
            self._activate()

    def _move(self, direction):
        n = len(self._menu)
        old_selected = self._selected
        index = self._selected

        for _ in range(n):
            index = (index + direction) % n
            if self._menu[index]["enabled"]:
                break

        if index != old_selected:
            self._selected = index
            self._refresh_highlight()
            
            if self.screen_manager._scene and hasattr(self.screen_manager._scene, 'sfx_manager'):
                self.screen_manager._scene.sfx_manager.play("snd_choice")

    def _activate(self):
        action = self._menu[self._selected]["action"]
        sm = self.screen_manager

        if sm._scene and hasattr(sm._scene, 'sfx_manager'):
            sfx = sm._scene.sfx_manager
            if action.startswith("slot"):
                sfx.play("snd_start")
            elif action == "back":
                sfx.play("snd_reject")

        self._dispatch(action)


    # ---------------------------------------------------------
    # SOURIS
    # ---------------------------------------------------------

    def mouse_press(self, scene_pos):

        for i, btn in enumerate(self._btns):

            if not self._menu[i]["enabled"]:
                continue

            if QRectF(
                _BTN_X,
                btn["y"],
                _BTN_W,
                _BTN_H
            ).contains(scene_pos):

                self._selected = i

                self._refresh_highlight()

                self._dispatch(
                    self._menu[i]["action"]
                )

                return

    # ---------------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------------


    def _dispatch(self, action):
        sm = self.screen_manager

        if action == "slot1":
            sm.load_game(1)
        elif action == "slot2":
            sm.load_game(2)
        elif action == "slot3":
            sm.load_game(3)
        elif action == "back":
            sm.go_to_title()