# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN, TITLE_BG_PATH, GAME_TITLE
from game.fonts import get_font0
from game.save_manager import SaveManager


class TitleScreen(BaseScreen):

    _menu_start_ratio = 0.50
    _menu_spacing     = 4

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = [
            {"label": "Nouvelle Partie", "action": "new_game",  "enabled": True},
            {"label": "Continuer",       "action": "continue",  "enabled": SaveManager.any_save_exists()},
            {"label": "Paramètres",      "action": "settings",  "enabled": True},
            {"label": "Quitter",         "action": "quit",      "enabled": True},
        ]

    def _build(self):
        self._build_background()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()
        self._play_title_music()

    def _build_background(self):
        pix = QPixmap(TITLE_BG_PATH)
        if not pix.isNull():
            bg = QGraphicsPixmapItem(
                pix.scaled(self.scene_w, self.scene_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        else:
            bg = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
            bg.setBrush(QBrush(QColor(10, 10, 30)))
            bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_SCREEN)
        self._items.append(bg)

    def _build_title(self):
        title = QGraphicsTextItem(GAME_TITLE)
        title.setFont(get_font0(size=16))
        title.setDefaultTextColor(QColor(255, 215, 0))
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos((self.scene_w - tw) / 2, int(self.scene_h * 0.18))
        self._items.append(title)

    def _activate(self):
        action = self._menu[self._selected]["action"]
        if action == "new_game":
            self._play_sfx("snd_start")
        elif action in ("continue", "settings"):
            self._play_sfx("snd_accept")
        self._dispatch(action)

    def _dispatch(self, action):
        sm = self.screen_manager
        if action == "new_game":
            sm.start_new_game()
        elif action == "continue":
            sm.show_screen("save_select")
        elif action == "settings":
            sm.go_to_settings()
        elif action == "quit":
            sm.quit_game()

    def _play_title_music(self):
        sm = self.screen_manager
        if hasattr(sm, 'music_manager'):
            sm.music_manager.play("mus_title", fade_in=0)
