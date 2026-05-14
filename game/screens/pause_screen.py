# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen, _SCENE_W, _SCENE_H
from game.config import Z_SCREEN, KEYS
from game.fonts import get_font0


class PauseScreen(BaseScreen):

    _menu_start_ratio = 0.38
    _menu_spacing     = 3

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = [
            {"label": "Reprendre",          "action": "resume",   "enabled": True},
            {"label": "Paramètres",          "action": "settings", "enabled": True},
            {"label": "Menu principal",      "action": "title",    "enabled": True},
            {"label": "Dernière Save", "action": "save",     "enabled": False},
            {"label": "Quitter",             "action": "quit",     "enabled": True},
        ]

    def _build(self):
        self._build_overlay()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
        overlay.setBrush(QBrush(QColor(0, 0, 0, 160)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_title(self):
        title = QGraphicsTextItem("Pause")
        title.setFont(get_font0(size=14))
        title.setDefaultTextColor(QColor(180, 180, 255))
        title.setZValue(Z_SCREEN + 1)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, int(_SCENE_H * 0.18))
        self._items.append(title)

    def key_press(self, key):
        if key in (KEYS["PAUSE"], KEYS["LEAVE"]):
            self.screen_manager.resume_game()
        else:
            super().key_press(key)

    def key_release(self, key):
        if key in (KEYS["PAUSE"], KEYS["LEAVE"]):
            return
        super().key_release(key)

    def _activate(self):
        action = self._menu[self._selected]["action"]
        if action not in ("resume", "quit"):
            self._play_sfx("snd_accept")
        self._dispatch(action)

    def _dispatch(self, action):
        sm = self.screen_manager
        if action == "resume":
            sm.resume_game()
        elif action == "settings":
            sm.go_to_settings()
        elif action == "title":
            sm.go_to_title()
            if hasattr(sm, 'music_manager'):
                sm.music_manager.play("mus_title")
        elif action == "save":
            current_slot = sm._scene.current_save.slot
            if current_slot:
                sm.load_game(current_slot)
        elif action == "quit":
            sm.quit_game()

    def show(self, scene):
        """
        cette fonction permet de recharger ecran lorsqu'on l'ouvre
        """
        has_slot = scene.current_save is not None and scene.current_save.slot is not None
        
        # mise a jour du slot
        for item in self._menu:
            if item["action"] == "save":
                item["enabled"] = has_slot
        
        if self._items:
            for item in self._items:
                if item.scene():
                    item.scene().removeItem(item)
            self._items.clear()
            
        self._build()
        super().show(scene)
