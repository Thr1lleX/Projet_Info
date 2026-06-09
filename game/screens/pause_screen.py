# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN
from game.fonts import get_font0
from game.settings import settings


class PauseScreen(BaseScreen):
    """Ecran de pause s'affichant en superposition pendant une partie."""

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
        """Cree le fond assombri, le titre et le menu de pause."""
        self._build_overlay()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
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
        title.setPos((self.scene_w - tw) / 2, int(self.scene_h * 0.18))
        self._items.append(title)

    def key_press(self, key):
        """Gere les raccourcis pour reprendre la partie ou naviguer dans le menu."""
        if key in (settings.keys["PAUSE"], settings.keys["LEAVE"]):
            self.screen_manager.resume_game()
        else:
            super().key_press(key)

    def key_release(self, key):
        """Evite les comportements indesirables lors du relachement des touches de pause."""
        if key in (settings.keys["PAUSE"], settings.keys["LEAVE"]):
            return
        super().key_release(key)

    def _activate(self):
        """Joue un son de validation (sauf exceptions) puis execute l'action selectionnee."""
        action = self._menu[self._selected]["action"]
        if action not in ("resume", "quit"):
            self._play_sfx("snd_accept")
        self._dispatch(action)

    def _dispatch(self, action):
        """Dispatche l'action selectionnee vers le gestionnaire d'ecran."""
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
        """Met a jour la disponibilite du bouton de sauvegarde puis affiche l'ecran."""
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
