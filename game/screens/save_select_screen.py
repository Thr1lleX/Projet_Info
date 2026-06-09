# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN, TITLE_BG_PATH
from game.fonts import get_font0
from game.save_manager import SaveManager


class SaveSelectScreen(BaseScreen):
    """Ecran interactif de l'ecran titre permettant de charger une sauvegarde existante."""

    _menu_start_ratio = 0.50
    _menu_spacing     = 4

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._menu = []

    def _build(self):
        """Met a jour les slots disponibles, cree le fond, le titre et le menu de selection."""
        self._refresh_slots()
        self._build_background()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()


    def _build_background(self):
        """Cree l'arriere-plan du menu de selection de sauvegarde."""
        pixmap = QPixmap("assets/hud/settings_background.png")
        pixmap = pixmap.scaled(self.scene_w, self.scene_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        bg = QGraphicsPixmapItem(pixmap)
        bg.setZValue(Z_SCREEN - 1)
        self._items.append(bg)
        
    def _build_title(self):
        """Cree et centre le titre de l'ecran de selection de sauvegarde."""
        title = QGraphicsTextItem("Choisir une\nsauvegarde")
    
        title.setFont(get_font0(size=12))
        title.setDefaultTextColor(QColor(22, 40, 59))
        title.setZValue(Z_SCREEN + 1)
    
        # largeur fixe pour permettre l'alignement
        title.setTextWidth(self.scene_w)
    
        # centrage horizontal du texte
        option = title.document().defaultTextOption()
        option.setAlignment(Qt.AlignHCenter)
        title.document().setDefaultTextOption(option)
    
        title.setPos(0, int(self.scene_h * 0.18))
    
        self._items.append(title)


    def _activate(self):
        """Joue un son specifique et declenche l'action de chargement ou de retour."""
        action = self._menu[self._selected]["action"]
        if action.startswith("slot"):
            self._play_sfx("snd_start")
        elif action == "back":
            self._play_sfx("snd_reject")
        self._dispatch(action)

    def _dispatch(self, action):
        """Charge la sauvegarde selectionnee ou retourne a l'ecran titre."""
        sm = self.screen_manager
        if action == "slot1":
            sm.load_game(1)
        elif action == "slot2":
            sm.load_game(2)
        elif action == "slot3":
            sm.load_game(3)
        elif action == "back":
            sm.go_to_title()
    
    def _refresh_slots(self):
        """Met a jour la liste des sauvegardes disponibles a chaque fois qu'on ouvre l'ecran."""
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
            },
        ]
    
        self._select_first_enabled()
        
    def show(self, scene):
        """Recharge l'ecran avec les donnees a jour lors de son affichage."""
        self._refresh_slots()
        
        # si ecran deja construit on nettoie anciens items
        if self._items:
            for item in self._items:
                if item.scene():
                    item.scene().removeItem(item)
            self._items.clear()

        self._build()
        
        super().show(scene)
