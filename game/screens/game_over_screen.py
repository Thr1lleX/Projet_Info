# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen, _SCENE_W, _SCENE_H
from game.config import Z_SCREEN
from game.fonts import get_font0


class GameOverScreen(BaseScreen):

    _menu_start_ratio = 0.52
    _menu_spacing     = 4

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = [
            {"label": "Recommencer",        "action": "restart",   "enabled": True},
            {"label": "Retour au menu",      "action": "menu",      "enabled": True},
            {"label": "Point de sauvegarde", "action": "load_save", "enabled": False},
            {"label": "Quitter",             "action": "quit",      "enabled": True},
        ]

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
        title.setFont(get_font0(size=14))
        title.setDefaultTextColor(QColor(200, 30, 30))
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, int(_SCENE_H * 0.26))
        self._items.append(title)

    def _activate(self):
        action = self._menu[self._selected]["action"]
        if action == "restart":
            self._play_sfx("snd_start")
        elif action not in ("restart", "quit"):
            self._play_sfx("snd_accept")
        self._dispatch(action)

    def _dispatch(self, action):
        sm = self.screen_manager
        if action == "restart":
            sm.start_new_game()
        elif action == "menu":
            sm.go_to_title()
        elif action == "load_save":
            pass
        elif action == "quit":
            sm.quit_game()