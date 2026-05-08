# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen, _SCENE_W, _SCENE_H
from game.config import Z_SCREEN, TITLE_BG_PATH
from game.fonts import get_font0
from game.save_manager import SaveManager


class SaveSelectScreen(BaseScreen):

    _menu_start_ratio = 0.50
    _menu_spacing     = 4

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = [
            {"label": "Partie 1", "action": "slot1", "enabled": SaveManager.save_exists(1)},
            {"label": "Partie 2", "action": "slot2", "enabled": SaveManager.save_exists(2)},
            {"label": "Partie 3", "action": "slot3", "enabled": SaveManager.save_exists(3)},
            {"label": "Retour",   "action": "back",  "enabled": True},
        ]
        self._select_first_enabled()

    def _build(self):
        self._build_background()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_background(self):
        pix = QPixmap(TITLE_BG_PATH)
        if not pix.isNull():
            bg = QGraphicsPixmapItem(
                pix.scaled(_SCENE_W, _SCENE_H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        else:
            bg = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
            bg.setBrush(QBrush(QColor(10, 10, 30)))
            bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_SCREEN)
        self._items.append(bg)

    def _build_title(self):
        title = QGraphicsTextItem("Choisir une sauvegarde")
        title.setFont(get_font0(size=12))
        title.setDefaultTextColor(QColor(255, 215, 0))
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, int(_SCENE_H * 0.18))
        self._items.append(title)

    def _activate(self):
        action = self._menu[self._selected]["action"]
        if action.startswith("slot"):
            self._play_sfx("snd_start")
        elif action == "back":
            self._play_sfx("snd_reject")
        self._dispatch(action)

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