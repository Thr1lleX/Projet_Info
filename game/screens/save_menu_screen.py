# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsRectItem,QGraphicsPixmapItem,QGraphicsTextItem
from PyQt5.QtGui import QBrush,QColor,QPen,QPixmap

from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen, _SCENE_W,_SCENE_H

from game.config import Z_SCREEN,TITLE_BG_PATH

from game.fonts import get_font0


class SaveMenuScreen(BaseScreen):

    _menu_start_ratio = 0.50
    _menu_spacing = 4

    def __init__(self, screen_manager):

        super().__init__(screen_manager)

        self._menu = [

            {
                "label": "Sauver partie 1",
                "action": "slot1",
                "enabled": True
            },

            {
                "label": "Sauver partie 2",
                "action": "slot2",
                "enabled": True
            },

            {
                "label": "Sauver partie 3",
                "action": "slot3",
                "enabled": True
            },

            {
                "label": "Retour",
                "action": "back",
                "enabled": True
            }
        ]

        self._selected = 0

    def _build(self):

        self._build_background()
        self._build_title()
        self._build_menu()
        self._refresh_highlight()

    def _build_background(self):

        bg = QGraphicsRectItem(
            0,
            0,
            _SCENE_W,
            _SCENE_H
        )

        bg.setBrush(
            QBrush(QColor(0, 0, 0, 180))
        )

        bg.setPen(QPen(Qt.NoPen))

        bg.setZValue(Z_SCREEN)

        self._items.append(bg)

    def _build_title(self):
    
        title = QGraphicsTextItem("Choisir un\nemplacement")
    
        title.setFont(get_font0(size=11))
        title.setDefaultTextColor(QColor(255, 215, 0))
        title.setZValue(Z_SCREEN + 1)
    
        # largeur fixe pour permettre l'alignement
        title.setTextWidth(_SCENE_W)
    
        # centrage horizontal du texte
        option = title.document().defaultTextOption()
        option.setAlignment(Qt.AlignHCenter)
        title.document().setDefaultTextOption(option)
    
        title.setPos(0, int(_SCENE_H * 0.18))
    
        self._items.append(title)

    def _activate(self):
        action = self._menu[self._selected]["action"]
        if action.startswith("slot"):
            self._play_sfx("snd_save")

        elif action == "back":
            self._play_sfx("snd_reject")

        self._dispatch(action)


    def _dispatch(self, action):
        sm = self.screen_manager
        if action == "slot1":
            sm.scene.save_game(1)
            sm.close_save_menu()
        elif action == "slot2":
            sm.scene.save_game(2)
            sm.close_save_menu()
        elif action == "slot3":
            sm.scene.save_game(3)
            sm.close_save_menu()
        elif action == "back":
            sm.close_save_menu()
            

    