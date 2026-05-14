# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QKeySequence
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen, _SCENE_W, _SCENE_H
from game.config import TILE_SIZE, Z_SCREEN, KEYS
from game.fonts import get_font0
from game.ui.option_row import OptionRow
from game.ui.sprite_button import SpriteButton

# --- Options disponibles pour chaque parametre ---
_VOLUME_OPTIONS = [
    ("Muet",  0.0),
    ("Bas",   0.25),
    ("Moyen", 0.50),
    ("Élevé", 0.75),
    ("Max",   1.0),
]

_CRT_OPTIONS = [
    ("Non", False),
    ("Oui", True),
]

_ANIM_OPTIONS = [
    ("Lente",   0.8),
    ("Normale", 0.5),
    ("Rapide",  0.2),
]

# --- Geometrie du panneau (en tiles) ---
_PANEL_W_TILES = 12
_PANEL_H_TILES = 9


class SettingsScreen(BaseScreen):

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._rows       = []   # liste d'OptionRow
        self._apply_btn  = None # SpriteButton
        self._selected   = 0    # index dans _rows + [_apply_btn]
        self._nav_count  = 0    # nombre total d'elements navigables

    # ------------------------------------------------------------------
    # cycle de vie
    # ------------------------------------------------------------------

    def show(self, scene):
        super().show(scene)
        self._load_current_values()
        self._refresh_all()

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def _build(self):
        self._build_background()
        self._build_overlay()
        self._build_panel()
        self._build_title()
        self._build_options()
        self._build_apply_button()
        self._build_hint()
        self._nav_count = len(self._rows) + 1   # +1 pour le bouton Appliquer

    # --- fond et panneau ---

    def _build_background(self):
        pixmap = QPixmap("assets/hud/settings_background.png")
        pixmap = pixmap.scaled(_SCENE_W, _SCENE_H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        bg = QGraphicsPixmapItem(pixmap)
        bg.setZValue(Z_SCREEN - 1)
        self._items.append(bg)

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
        overlay.setBrush(QBrush(QColor(8, 8, 20, 200)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_panel(self):
        pw = _PANEL_W_TILES * TILE_SIZE
        ph = _PANEL_H_TILES * TILE_SIZE
        px = (_SCENE_W - pw) // 2
        py = (_SCENE_H - ph) // 2
        panel = QGraphicsRectItem(px, py, pw, ph)
        panel.setBrush(QBrush(QColor(20, 20, 40, 250)))
        panel.setPen(QPen(QColor(80, 80, 130), 2))
        panel.setZValue(Z_SCREEN + 1)
        self._items.append(panel)

    def _build_title(self):
        title = QGraphicsTextItem("Paramètres")
        title.setFont(get_font0(size=12))
        title.setDefaultTextColor(QColor(180, 180, 255))
        title.setZValue(Z_SCREEN + 2)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, self._panel_y() + TILE_SIZE * 0.3)
        self._items.append(title)

    # --- lignes d'options ---

    def _build_options(self):
        px       = self._panel_x()
        x_label  = px + TILE_SIZE          # 1 tile de marge a gauche
        x_value  = px + 6 * TILE_SIZE      # valeur dans la moitie droite
        val_w    = 5 * TILE_SIZE           # largeur zone valeur
        start_y  = self._panel_y() + int(TILE_SIZE * 2)
        row_gap  = int(TILE_SIZE * 1.2)

        definitions = [
            ("Volume musique :", _VOLUME_OPTIONS),
            ("Volume effets :",  _VOLUME_OPTIONS),
            ("Effet CRT :",      _CRT_OPTIONS),
            ("Anim. tuiles :",   _ANIM_OPTIONS),
        ]

        self._rows = []
        for i, (label, options) in enumerate(definitions):
            y = start_y + i * row_gap
            row = OptionRow(label, options, x_label, x_value, y, val_w)
            self._rows.append(row)
            self._items.extend(row.get_items())

    # --- bouton Appliquer ---

    def _build_apply_button(self):
        btn_w = 7 * TILE_SIZE
        btn_x = (_SCENE_W - btn_w) // 2
        btn_y = self._panel_y() + int(TILE_SIZE * 7)
        self._apply_btn = SpriteButton("Appliquer", btn_x, btn_y)
        self._items.extend(self._apply_btn.get_items())

    # --- texte d'indication ---

    def _build_hint(self):
        key1 = QKeySequence(KEYS["LEAVE"]).toString()
        key2 = QKeySequence(KEYS["PAUSE"]).toString()
        hint = QGraphicsTextItem(f"{key1} / {key2} pour annuler")
        hint.setFont(get_font0(size=3))
        hint.setDefaultTextColor(QColor(120, 120, 140))
        hint.setZValue(Z_SCREEN + 2)
        tw = hint.boundingRect().width()
        hint.setPos((_SCENE_W - tw) / 2, self._panel_y() + int(TILE_SIZE * 8.2))
        self._items.append(hint)

    # --- helpers de position ---

    def _panel_x(self):
        return (_SCENE_W - _PANEL_W_TILES * TILE_SIZE) // 2

    def _panel_y(self):
        return (_SCENE_H - _PANEL_H_TILES * TILE_SIZE) // 2

    # ------------------------------------------------------------------
    # chargement des valeurs depuis SettingsManager
    # ------------------------------------------------------------------

    def _load_current_values(self):
        settings = getattr(self.screen_manager, 'settings', None)
        if settings is None or not self._rows:
            return
        self._rows[0].set_value(settings.music_volume)
        self._rows[1].set_value(settings.sfx_volume)
        self._rows[2].set_value(settings.crt_overlay)
        self._rows[3].set_value(settings.tile_anim_speed)

    # ------------------------------------------------------------------
    # rafraichissement visuel
    # ------------------------------------------------------------------

    def _refresh_all(self):
        for i, row in enumerate(self._rows):
            row.set_selected(i == self._selected)
        is_on_btn = (self._selected == len(self._rows))
        self._apply_btn.set_state("selected" if is_on_btn else "normal")

    # ------------------------------------------------------------------
    # navigation clavier
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key in (KEYS["PAUSE"], KEYS["LEAVE"]):
            self._cancel()
        elif key == KEYS["UP"]:
            self._nav(-1)
        elif key == KEYS["DOWN"]:
            self._nav(+1)
        elif key == KEYS["LEFT"]:
            self._cycle(-1)
        elif key == KEYS["RIGHT"]:
            self._cycle(+1)
        elif key in (KEYS["ATTACK"], KEYS["INTERACT"], KEYS["CONFIRM"]):
            self._press_current()

    def key_release(self, key):
        if key in (KEYS["ATTACK"], KEYS["INTERACT"], KEYS["CONFIRM"]):
            self._release_current()

    def _nav(self, direction):
        old = self._selected
        self._selected = (self._selected + direction) % self._nav_count
        if self._selected != old:
            self._refresh_all()
            self._play_sfx("snd_choice")

    def _cycle(self, direction):
        if self._selected < len(self._rows):
            self._rows[self._selected].cycle(direction)
            self._play_sfx("snd_choice")

    def _press_current(self):
        if self._selected == len(self._rows):
            self._apply_btn.set_state("pressed")
            self._is_pressed = True

    def _release_current(self):
        if self._is_pressed:
            self._is_pressed = False
            self._apply_btn.set_state("selected")
            self._apply()

    # ------------------------------------------------------------------
    # navigation souris
    # ------------------------------------------------------------------

    def mouse_press(self, scene_pos):
        from PyQt5.QtCore import QRectF
        # clic sur une ligne d'option
        for i, row in enumerate(self._rows):
            px = self._panel_x()
            rect = QRectF(px, row.y, _PANEL_W_TILES * TILE_SIZE, row.height)
            if rect.contains(scene_pos):
                self._selected = i
                self._refresh_all()
                return
        # clic sur Appliquer
        if self._apply_btn.contains(scene_pos):
            self._selected = len(self._rows)
            self._refresh_all()
            self._apply_btn.set_state("pressed")
            self._apply()

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------

    def _apply(self):
        settings = getattr(self.screen_manager, 'settings', None)
        if settings is None:
            self.screen_manager.back_from_settings()
            return

        settings.music_volume    = self._rows[0].get_value()
        settings.sfx_volume      = self._rows[1].get_value()
        settings.crt_overlay     = self._rows[2].get_value()
        settings.tile_anim_speed = self._rows[3].get_value()

        settings.save()

        scene = self.screen_manager.scene
        if scene is not None:
            settings.apply_to_scene(scene)
    

        self.screen_manager.back_from_settings()

    def _cancel(self):
        self.screen_manager.back_from_settings()
