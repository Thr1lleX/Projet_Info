# -*- coding: utf-8 -*-
"""
Ecran des parametres (complet).

Utilise QGraphicsProxyWidget pour integrer les controles Qt (sliders,
cases a cocher, liste deroulante, boutons) directement dans la QGraphicsScene.

Flux :
  show()       → construit une fois (_build), puis actualise les widgets
                  depuis SettingsManager (_refresh_widget_values).
  [Appliquer]  → lit les widgets, met a jour SettingsManager, sauvegarde,
                  applique a la scene et a la fenetre, puis retourne.
  [Annuler]    → retourne sans appliquer.
  Echap        → equivalent a Annuler.

Options disponibles :
  - Volume musique    (QSlider 0-100)
  - Volume effets SFX (QSlider 0-100)
  - Effet CRT         (QCheckBox)
  - Plein ecran       (QCheckBox)
  - Debug hitboxes    (QCheckBox)
  - Vitesse anim.     (QComboBox : Lente / Normale / Rapide)

Pour ajouter une option :
  1. Ajouter le widget dans la methode _build_xxx() correspondante.
  2. Lire/ecrire la valeur dans _refresh_widget_values() et _apply().
"""

from PyQt5.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsProxyWidget,
    QSlider, QCheckBox, QComboBox, QPushButton,
)
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE, Z_SCREEN
from game.fonts import get_font0

_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

# --- geometrie du panneau ---
_PANEL_W = 560
_PANEL_H = 460
_PANEL_X = (_SCENE_W - _PANEL_W) // 2
_PANEL_Y = (_SCENE_H - _PANEL_H) // 2

_LABEL_X  = _PANEL_X + 24
_WIDGET_X = _PANEL_X + 230
_WIDGET_W = _PANEL_W - 230 - 28   # ~302px

# lignes Y successives (relatives a la scene, pas au panneau)
_ROW_TITLE   = _PANEL_Y + 18
_ROW_MUS     = _PANEL_Y + 90
_ROW_SFX     = _PANEL_Y + 138
_ROW_CRT     = _PANEL_Y + 196
_ROW_FULL    = _PANEL_Y + 238
_ROW_DEBUG   = _PANEL_Y + 280
_ROW_ANIM    = _PANEL_Y + 332
_ROW_BTNS    = _PANEL_Y + 396

_BTN_W = 130
_BTN_H = 42

# correspondances vitesse <-> index combo
_ANIM_SPEEDS = [("Lente", 0.8), ("Normale", 0.5), ("Rapide", 0.2)]

# feuille de style commune a tous les widgets de cet ecran
_STYLE = (
    "QSlider::groove:horizontal { height:6px; background:#404060; border-radius:3px; }"
    "QSlider::handle:horizontal  { width:14px; height:14px; margin:-4px 0;"
    "                               background:#8888dd; border-radius:7px; }"
    "QSlider::sub-page:horizontal { background:#6666bb; border-radius:3px; }"
    "QCheckBox { color:#c8c8e0; spacing:8px; }"
    "QCheckBox::indicator         { width:16px; height:16px; background:#303050;"
    "                               border:1px solid #7070b0; border-radius:3px; }"
    "QCheckBox::indicator:checked { background:#6666bb; }"
    "QComboBox { background:#303050; border:1px solid #7070b0; border-radius:4px;"
    "            padding:3px 8px; color:#c8c8e0; min-width:120px; }"
    "QComboBox QAbstractItemView  { background:#303050; color:#c8c8e0;"
    "                               selection-background-color:#6666bb; }"
    "QPushButton { background:#303050; border:1px solid #7070b0; border-radius:6px;"
    "              color:#c8c8e0; padding:6px 16px; }"
    "QPushButton:hover   { background:#444470; }"
    "QPushButton:pressed { background:#6666bb; }"
)

_C_TITLE = QColor(180, 180, 255)
_C_LABEL = QColor(190, 190, 210)


class SettingsScreen(BaseScreen):
    """Ecran parametres avec controles Qt integres via QGraphicsProxyWidget."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        # references aux widgets (remplies dans _build)
        self._sl_music = None
        self._sl_sfx   = None
        self._cb_crt   = None
        self._cb_full  = None
        self._cb_debug = None
        self._cmb_anim = None

    # ------------------------------------------------------------------
    # cycle de vie
    # ------------------------------------------------------------------

    def show(self, scene):
        """Construit (si necessaire) puis actualise les valeurs des widgets."""
        super().show(scene)
        self._refresh_widget_values()

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def _build(self):
        self._build_overlay()
        self._build_panel()
        self._build_title()
        self._build_volume_rows()
        self._build_checkbox_rows()
        self._build_anim_row()
        self._build_buttons()

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
        overlay.setBrush(QBrush(QColor(8, 8, 20, 200)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_panel(self):
        panel = QGraphicsRectItem(_PANEL_X, _PANEL_Y, _PANEL_W, _PANEL_H)
        panel.setBrush(QBrush(QColor(20, 20, 40, 250)))
        panel.setPen(QPen(QColor(80, 80, 130), 2))
        panel.setZValue(Z_SCREEN + 1)
        self._items.append(panel)

    def _build_title(self):
        title = QGraphicsTextItem("Parametres")
        title.setFont(get_font0(size=46))
        title.setDefaultTextColor(_C_TITLE)
        title.setZValue(Z_SCREEN + 2)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, _ROW_TITLE)
        self._items.append(title)

    # --- helpers internes ---

    def _add_label(self, text, y):
        lbl = QGraphicsTextItem(text)
        lbl.setFont(get_font0(size=18))
        lbl.setDefaultTextColor(_C_LABEL)
        lbl.setZValue(Z_SCREEN + 2)
        lbl.setPos(_LABEL_X, y)
        self._items.append(lbl)

    def _add_proxy(self, widget, x, y, w=None, h=None):
        """Enveloppe un widget Qt dans un QGraphicsProxyWidget et l'ajoute a self._items."""
        widget.setStyleSheet(_STYLE)
        if w is not None:
            widget.setFixedWidth(w)
        if h is not None:
            widget.setFixedHeight(h)
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(widget)
        proxy.setPos(x, y)
        proxy.setZValue(Z_SCREEN + 3)
        self._items.append(proxy)
        return proxy

    # --- lignes de controles ---

    def _build_volume_rows(self):
        self._add_label("Volume musique :", _ROW_MUS + 2)
        self._sl_music = QSlider(Qt.Horizontal)
        self._sl_music.setRange(0, 100)
        self._add_proxy(self._sl_music, _WIDGET_X, _ROW_MUS, _WIDGET_W, 28)

        self._add_label("Volume effets :", _ROW_SFX + 2)
        self._sl_sfx = QSlider(Qt.Horizontal)
        self._sl_sfx.setRange(0, 100)
        self._add_proxy(self._sl_sfx, _WIDGET_X, _ROW_SFX, _WIDGET_W, 28)

    def _build_checkbox_rows(self):
        self._cb_crt = QCheckBox("Effet CRT")
        self._add_proxy(self._cb_crt, _LABEL_X, _ROW_CRT, h=28)

        self._cb_full = QCheckBox("Plein ecran")
        self._add_proxy(self._cb_full, _LABEL_X, _ROW_FULL, h=28)

        self._cb_debug = QCheckBox("Debug hitboxes")
        self._add_proxy(self._cb_debug, _LABEL_X, _ROW_DEBUG, h=28)

    def _build_anim_row(self):
        self._add_label("Anim. tuiles :", _ROW_ANIM + 2)
        self._cmb_anim = QComboBox()
        for label, _ in _ANIM_SPEEDS:
            self._cmb_anim.addItem(label)
        self._add_proxy(self._cmb_anim, _WIDGET_X, _ROW_ANIM, 140, 28)

    def _build_buttons(self):
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self._cancel)
        self._add_proxy(btn_cancel, _PANEL_X + 60, _ROW_BTNS, _BTN_W, _BTN_H)

        btn_apply = QPushButton("Appliquer")
        btn_apply.clicked.connect(self._apply)
        self._add_proxy(btn_apply, _PANEL_X + _PANEL_W - 60 - _BTN_W, _ROW_BTNS, _BTN_W, _BTN_H)

    # ------------------------------------------------------------------
    # actualisation des valeurs depuis SettingsManager
    # ------------------------------------------------------------------

    def _refresh_widget_values(self):
        """Charge les valeurs courantes du SettingsManager dans les widgets."""
        settings = getattr(self.screen_manager, 'settings', None)
        if settings is None or self._sl_music is None:
            return
        self._sl_music.setValue(int(settings.music_volume * 100))
        self._sl_sfx.setValue(int(settings.sfx_volume * 100))
        self._cb_crt.setChecked(settings.crt_overlay)
        self._cb_full.setChecked(settings.fullscreen)
        self._cb_debug.setChecked(settings.debug_hitboxes)
        speed = settings.tile_anim_speed
        for i, (_, val) in enumerate(_ANIM_SPEEDS):
            if abs(val - speed) < 0.01:
                self._cmb_anim.setCurrentIndex(i)
                break

    # ------------------------------------------------------------------
    # actions des boutons
    # ------------------------------------------------------------------

    def _apply(self):
        """Lit les widgets, sauvegarde et applique les changements."""
        settings = getattr(self.screen_manager, 'settings', None)
        if settings is None:
            self.screen_manager.back_from_settings()
            return

        settings.music_volume    = self._sl_music.value() / 100.0
        settings.sfx_volume      = self._sl_sfx.value()   / 100.0
        settings.crt_overlay     = self._cb_crt.isChecked()
        settings.fullscreen      = self._cb_full.isChecked()
        settings.debug_hitboxes  = self._cb_debug.isChecked()
        settings.tile_anim_speed = _ANIM_SPEEDS[self._cmb_anim.currentIndex()][1]

        settings.save()

        scene = self.screen_manager.scene
        if scene is not None:
            settings.apply_to_scene(scene)
        settings.apply_to_window(self.screen_manager.window)

        self.screen_manager.back_from_settings()

    def _cancel(self):
        self.screen_manager.back_from_settings()

    # ------------------------------------------------------------------
    # evenements clavier
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key == Qt.Key_Escape:
            self._cancel()
