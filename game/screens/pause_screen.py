# -*- coding: utf-8 -*-
"""
Ecran de pause.

S'ouvre avec Echap pendant le jeu, ferme le jeu derriere un voile semi-transparent.
La musique est baissee pendant la pause (voir ScreenManager.open_pause).

Options de menu :
  - Reprendre          → reprend la partie
  - Parametres         → ouvre l'ecran des parametres
  - Menu principal     → retourne au titre
  - Point de sauvegarde (grise, non implante)
  - Quitter            → ferme l'application

Navigation : fleches haut/bas + Entree, Echap = Reprendre, clic souris.
"""

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt, QRectF

from game.screens.base_screen import BaseScreen
from game.config import GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE, Z_SCREEN, KEYS
from game.fonts import get_font0

_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

_BTN_W       = 320
_BTN_H       = 48
_BTN_SPACING = 12
_BTN_X       = (_SCENE_W - _BTN_W) // 2
_FIRST_BTN_Y = int(_SCENE_H * 0.38)

_C_OVERLAY    = QColor(0, 0, 0, 160)        # voile semi-transparent
_C_BG_NORMAL  = QColor(20,  20,  50,  210)
_C_BG_SELECT  = QColor(70,  50,  10,  230)
_C_TXT_NORMAL = QColor(200, 200, 200)
_C_TXT_SELECT = QColor(255, 215,   0)
_C_TXT_DISABL = QColor(70,  70,  70)
_C_TITLE      = QColor(180, 180, 255)


class PauseScreen(BaseScreen):
    """Ecran de pause semi-transparent (le jeu reste visible en dessous)."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = [
            {"label": "Reprendre",           "action": "resume",   "enabled": True},
            {"label": "Paramètres",           "action": "settings", "enabled": True},
            {"label": "Menu principal",       "action": "title",    "enabled": True},
            {"label": "Point de sauvegarde",  "action": "save",     "enabled": False},
            {"label": "Quitter",              "action": "quit",     "enabled": True},
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
        overlay.setBrush(QBrush(_C_OVERLAY))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_title(self):
        title = QGraphicsTextItem("Pause")
        title.setFont(get_font0(size=56))
        title.setDefaultTextColor(_C_TITLE)
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, int(_SCENE_H * 0.18))
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
            text.setFont(get_font0(size=22))
            text.setZValue(Z_SCREEN + 2)
            color = _C_TXT_NORMAL if entry["enabled"] else _C_TXT_DISABL
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
                btn["rect"].setBrush(QBrush(_C_BG_SELECT))
                btn["text"].setDefaultTextColor(_C_TXT_SELECT)
            else:
                btn["rect"].setBrush(QBrush(_C_BG_NORMAL))
                btn["text"].setDefaultTextColor(_C_TXT_NORMAL)

    # ------------------------------------------------------------------
    # navigation clavier
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key in (KEYS["PAUSE"], KEYS["LEAVE"]):
            self.screen_manager.resume_game()
        elif key in (KEYS["DOWN"], KEYS["RIGHT"]):
            self._move(+1)
        elif key in (KEYS["UP"], KEYS["LEFT"]):
            self._move(-1)
        elif key in (KEYS["INTERACT"],KEYS["ATTACK"],KEYS["CONFIRM"]):
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
        
        if action not in ["resume", "quit"]:
            if self.screen_manager._scene and hasattr(self.screen_manager._scene, 'sfx_manager'):
                self.screen_manager._scene.sfx_manager.play("snd_accept")
        
        self._dispatch(action)

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
    # dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, action):
        sm = self.screen_manager
        if action == "resume":
            sm.resume_game()
        elif action == "settings":
            sm.go_to_settings()
        elif action == "title":
            sm.go_to_title()
        elif action == "quit":
            sm.quit_game()
