# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN
from game.fonts import get_font0


class GameOverScreen(BaseScreen):
    """Ecran de fin de partie proposant de recommencer, charger une sauvegarde ou quitter."""

    _menu_start_ratio = 0.52
    _menu_spacing     = 4

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = [
            {"label": "Recommencer",        "action": "restart",   "enabled": True},
            {"label": "Retour au menu",      "action": "menu",      "enabled": True},
            {"label": "Dernière Save", "action": "load_save", "enabled": False},
            {"label": "Quitter",             "action": "quit",      "enabled": True},
        ]

    def _build(self):
        """Cree le fond assombri, le titre et le menu de l'ecran de fin."""
        self._build_overlay()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
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
        title.setPos((self.scene_w - tw) / 2, int(self.scene_h * 0.26))
        self._items.append(title)

    def _activate(self):
        """Execute l'action du bouton selectionne et joue un son."""
        action = self._menu[self._selected]["action"]
        if action == "restart":
            self._play_sfx("snd_start")
        elif action not in ("restart", "quit"):
            self._play_sfx("snd_accept")
        self._dispatch(action)

    def _dispatch(self, action):
        """Dispatche l'action selectionnee vers le gestionnaire d'ecran."""
        sm = self.screen_manager
        
        # remettre la boucle de musique
        if action in ("restart","menu","load_save"):
            sm.music_manager.player.setLoopCount(-2)
        if action == "restart":
            sm.start_new_game()
        elif action == "menu":
            sm.go_to_title()
        elif action == "load_save":
            if sm._scene and sm._scene.current_save:
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
            if item["action"] == "load_save":
                item["enabled"] = has_slot
        
        if self._items:
            for item in self._items:
                if item.scene():
                    item.scene().removeItem(item)
            self._items.clear()
            
        self._build()
        super().show(scene)
