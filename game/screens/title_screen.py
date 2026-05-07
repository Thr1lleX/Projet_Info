# -*- coding: utf-8 -*-
"""
Ecran titre : fond, titre du jeu et menu principal.

Entrees de menu :
  - Nouvelle Partie  → demarre une partie
  - Continuer        → grisee (sauvegarde non implantee)
  - Parametres       → ouvre l'ecran des parametres
  - Quitter          → ferme l'application

Navigation : fleches haut/bas + Entree, ou clic souris.
"""

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt, QRectF

from game.screens.base_screen import BaseScreen
from game.config import (
    GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE,
    Z_SCREEN, TITLE_BG_PATH, GAME_TITLE,
    KEYS
)
from game.fonts import get_font0
from game.save_manager import SaveManager

_SCENE_W = GRID_WIDTH * TILE_SIZE                    # 1024
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE   # 832

# --- geometrie des boutons ---
_BTN_W       = 300
_BTN_H       = 52
_BTN_SPACING = 16                                    # gap vertical entre boutons
_BTN_X       = (_SCENE_W - _BTN_W) // 2             # centre horizontal
_FIRST_BTN_Y = int(_SCENE_H * 0.50)                 # y du premier bouton

# --- couleurs ---
_C_BG_NORMAL   = QColor(20,  20,  20,  180)
_C_BG_SELECTED = QColor(90,  60,  10,  220)
_C_TXT_NORMAL  = QColor(200, 200, 200)
_C_TXT_SELECT  = QColor(255, 215,   0)
_C_TXT_DISABLED= QColor(80,  80,  80)


class TitleScreen(BaseScreen):
    """Ecran titre avec menu de navigation."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        # definition du menu (ordre = ordre d'affichage)
        self._menu = [
            {"label": "Nouvelle Partie", "action": "new_game",  "enabled": True},
            # on grise si pas de save
            {
                "label": "Continuer",
                "action": "continue",
                "enabled": SaveManager.any_save_exists()
            },            
            #{"label": "Continuer",       "action": "continue",  "enabled": False},   # grise
            {"label": "Paramètres",      "action": "settings",  "enabled": True},
            {"label": "Quitter",         "action": "quit",      "enabled": True},
        ]
        self._selected = 0       # index de l'entree selectionnee au clavier
        self._btns     = []      # liste de dict {rect, text, y} par entree

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

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
                pix.scaled(_SCENE_W, _SCENE_H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        else:
            # fallback : fond degrade sombre si l'image n'existe pas encore
            bg = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
            bg.setBrush(QBrush(QColor(10, 10, 30)))
            bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_SCREEN)
        self._items.append(bg)

    def _build_title(self):
        title = QGraphicsTextItem(GAME_TITLE)
        title.setFont(get_font0(size=64))
        title.setDefaultTextColor(QColor(255, 215, 0))
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
            text.setFont(get_font0(size=24))
            text.setZValue(Z_SCREEN + 2)

            color = _C_TXT_NORMAL if entry["enabled"] else _C_TXT_DISABLED
            text.setDefaultTextColor(color)

            # centrage du texte dans le bouton
            tw = text.boundingRect().width()
            th = text.boundingRect().height()
            text.setPos(_BTN_X + (_BTN_W - tw) / 2, y + (_BTN_H - th) / 2)

            self._items.extend([rect, text])
            self._btns.append({"rect": rect, "text": text, "y": y})

    def _refresh_highlight(self):
        """Applique la couleur de selection a l'entree courante."""
        for i, btn in enumerate(self._btns):
            if not self._menu[i]["enabled"]:
                continue
            if i == self._selected:
                btn["rect"].setBrush(QBrush(_C_BG_SELECTED))
                btn["text"].setDefaultTextColor(_C_TXT_SELECT)
            else:
                btn["rect"].setBrush(QBrush(_C_BG_NORMAL))
                btn["text"].setDefaultTextColor(_C_TXT_NORMAL)

    # ------------------------------------------------------------------
    # navigation clavier
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key == KEYS["DOWN"]:
            self._move(+1)
        elif key == KEYS["UP"]:
            self._move(-1)
        elif key in (KEYS["ATTACK"], KEYS["INTERACT"], KEYS["CONFIRM"]):
            self._activate()

    def _move(self, direction):
        """Deplace la selection en sautant les entrees desactivees."""
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
        
        if self.screen_manager._scene and hasattr(self.screen_manager._scene, 'sfx_manager'):
            sfx = self.screen_manager._scene.sfx_manager
            
            if action == "new_game":
                sfx.play("snd_start")
            elif action in ["continue", "settings"]:
                sfx.play("snd_accept")
        
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
    # dispatch des actions
    # ------------------------------------------------------------------

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
        """Lance la musique du menu principal."""
        sm = self.screen_manager
        if hasattr(sm, 'music_manager'):
            sm.music_manager.play("mus_title", fade_in=0)