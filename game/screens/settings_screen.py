# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QRectF

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN
from game.fonts import get_font0
from game.ui.sprite_button import SpriteButton

from game.settings import settings

# --- Definitions des options ---
_RESOLUTION_OPTIONS = [("  x1 >", 2.0), ("< x1.5 >", 3.0), ("< x2  ", 4.0)]
_CONTROL_OPTIONS = [("< AZERTY >", "azerty"), ("< QWERTY >", "qwerty")]
_VOLUME_OPTIONS=[("  Muet >", 0.0), ("< Bas >", 0.25), ("< Moyen >", 0.50), ("< Élevé >", 0.75), ("< Max  ", 1.0)]

_PANEL_W_TILES = 12
_PANEL_H_TILES = 11

# =====================================================================
# Classes UI Locales pour gerer differents types de lignes
# =====================================================================

class BaseSettingRow:
    def __init__(self, label_text, x_label, x_center_val, y,enabled=True):
        self.y = y
        self.x_center_val = x_center_val
        self.height = int(settings.tile_size * 1.2)
        self.items = []
        self.enabled = enabled
        
        self.label_item = QGraphicsTextItem(label_text)
        self.label_item.setFont(get_font0(size=6))
        color = QColor(QColor(200, 200, 200)) if self.enabled else QColor(100, 100, 100)
        self.label_item.setDefaultTextColor(color)
        self.label_item.setPos(x_label, y)
        self.label_item.setZValue(Z_SCREEN + 2)
        self.items.append(self.label_item)
    
    def set_selected(self, selected):
        label_color = QColor(255, 255, 100) if selected else QColor(200, 200, 200)
        self.label_item.setDefaultTextColor(label_color)
    
        # valeur devient grise si disabled
        if not self.enabled:
            val_color = QColor(100, 100, 100)
        else:
            val_color = label_color
    
        self._update_val_color(val_color)

    def _update_val_color(self, color):
        pass

    def get_items(self):
        return self.items

    def handle_left_right(self, direction):
        """
        return True si un changement a eu lieu
        """
        return False

    def handle_confirm(self):
        return False


class TextChoiceRow(BaseSettingRow):
    def __init__(self, label_text, options, x_label, x_center_val, y, bounded=True,enabled=True):
        super().__init__(label_text, x_label, x_center_val, y,enabled)
        self.options = options
        self.bounded = bounded
        self.index = 0

        self.val_item = QGraphicsTextItem("")
        self.val_item.setFont(get_font0(size=6))
        self.val_item.setDefaultTextColor(QColor(200, 200, 200) if self.enabled else QColor(100, 100, 100))
        self.val_item.setZValue(Z_SCREEN + 2)
        self.items.append(self.val_item)
        
        self._update_text_and_pos()

    def _update_text_and_pos(self):
        """
        mettre a jour le texte et le centrer
        """
        self.val_item.setPlainText(self.options[self.index][0])
        text_w = self.val_item.boundingRect().width()
        self.val_item.setPos(self.x_center_val - (text_w / 2), self.y)

    def _update_val_color(self, color):
        self.val_item.setDefaultTextColor(color)

    def handle_left_right(self, direction):
        old_index = self.index
        if self.bounded:
            self.index = max(0, min(len(self.options) - 1, self.index + direction))
        else:
            self.index = (self.index + direction) % len(self.options)
        
        if self.index != old_index:
            self._update_text_and_pos()
            return True # cas ou changement
        return False # cas touche bord


class CheckboxRow(BaseSettingRow):
    def __init__(self, label_text, x_label, x_center_val, y):
        super().__init__(label_text, x_label, x_center_val, y)
        self.checked = False
        self.size = 1.5 * settings.tile_size

        self.box_item = QGraphicsPixmapItem()
        self.box_item.setPos(self.x_center_val - (self.size / 2), y - (settings.tile_size * 0.25))
        self.box_item.setZValue(Z_SCREEN + 2)
        self.items.append(self.box_item)
        self._update_pixmap()

    def _update_pixmap(self):
        path = "assets/hud/box_checked.png" if self.checked else "assets/hud/box.png"
        pixmap = QPixmap(path).scaled(self.size, self.size, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.box_item.setPixmap(pixmap)

    def handle_left_right(self, direction):
        self.checked = not self.checked
        self._update_pixmap()
        return True

    def handle_confirm(self):
        self.checked = not self.checked
        self._update_pixmap()
        return True

# =====================================================================
# Ecran des parametres
# =====================================================================

class SettingsScreen(BaseScreen):

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._rows       = []   
        self._apply_btn  = None 
        self._selected   = 0    
        self._nav_count  = 0    
        self._rescale_allowed = True

    def show(self, scene):
        if not self._built:
            self._build()
            self._built = True
        self.sync_ui_with_settings()
        super().show(scene)
        self._refresh_all()

    def sync_ui_with_settings(self):
        """
        Force chaque ligne à afficher la valeur actuelle stockée dans settings.py
        """
        # resolution (Index 0)
        self._rows[0].index = settings.resolution_index
        self._rows[0]._update_text_and_pos()
        
        # controles (Index 1)
        for idx, (label, val) in enumerate(_CONTROL_OPTIONS):
            if val == settings.control_scheme:
                self._rows[1].index = idx
                self._rows[1]._update_text_and_pos()
                break

        # volume musique (Index 2)
        for idx, (label, val) in enumerate(_VOLUME_OPTIONS):
            if val == settings.music_volume:
                self._rows[2].index = idx
                self._rows[2]._update_text_and_pos()
                break

        # volume SFX (Index 3)
        for idx, (label, val) in enumerate(_VOLUME_OPTIONS):
            if val == settings.sfx_volume:
                self._rows[3].index = idx
                self._rows[3]._update_text_and_pos()
                break

        # filtre CRT (Index 4)
        self._rows[4].checked = settings.crt_overlay
        self._rows[4]._update_pixmap()

    def _build(self):
        self._build_background()
        self._build_overlay()
        self._build_panel()
        self._build_title()
        self._build_options()
        self._build_apply_button()
        self._build_hint()
        self._nav_count = len(self._rows) + 1

    def _build_background(self):
        pixmap = QPixmap("assets/hud/settings_background.png")
        pixmap = pixmap.scaled(self.scene_w, self.scene_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        bg = QGraphicsPixmapItem(pixmap)
        bg.setZValue(Z_SCREEN - 1)
        self._items.append(bg)

    def _build_overlay(self):
        overlay = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
        overlay.setBrush(QBrush(QColor(8, 8, 20, 200)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

    def _build_panel(self):
        pw = _PANEL_W_TILES * settings.tile_size
        ph = _PANEL_H_TILES * settings.tile_size
        px = (self.scene_w - pw) // 2
        py = (self.scene_h - ph) // 2
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
        title.setPos((self.scene_w - tw) / 2, self._panel_y() + settings.tile_size * 0.3)
        self._items.append(title)

    def set_rescale_allowed(self, allowed):
        self._rescale_allowed = allowed
        if self._built:
            self.reset_build()

    def _build_options(self):
        px           = self._panel_x()
        x_label      = px + settings.tile_size          
        x_center_val = px + 9.5 * settings.tile_size
        start_y      = self._panel_y() + int(settings.tile_size * 2.2)
        row_gap      = int(settings.tile_size * 1.2)

        self._rows = []

        self._rows.append(TextChoiceRow("Résolution :", _RESOLUTION_OPTIONS, x_label, x_center_val, start_y, bounded=True, enabled=self._rescale_allowed))
        self._rows.append(TextChoiceRow("Contrôles :", _CONTROL_OPTIONS, x_label, x_center_val, start_y + row_gap, bounded=False))
        
        row_mus = TextChoiceRow("Volume Musique :", _VOLUME_OPTIONS, x_label, x_center_val, start_y + row_gap * 2, bounded=True)
        row_mus.index = 2
        row_mus._update_text_and_pos()
        self._rows.append(row_mus)

        row_sfx = TextChoiceRow("Volume SFX :", _VOLUME_OPTIONS, x_label, x_center_val, start_y + row_gap * 3, bounded=True)
        row_sfx.index = 2
        row_sfx._update_text_and_pos()
        self._rows.append(row_sfx)

        self._rows.append(CheckboxRow("Filtre CRT :", x_label, x_center_val, start_y + row_gap * 4))

        for row in self._rows:
            self._items.extend(row.get_items())

    def _build_apply_button(self):
        btn_w = 7 * settings.tile_size
        btn_x = (self.scene_w - btn_w) // 2
        btn_y = self._panel_y() + int(settings.tile_size * 8.5)
        self._apply_btn = SpriteButton("Appliquer", btn_x, btn_y)
        self._items.extend(self._apply_btn.get_items())

    def _build_hint(self):
        key1 = QKeySequence(settings.keys["LEAVE"]).toString()
        key2 = QKeySequence(settings.keys["PAUSE"]).toString()
        hint = QGraphicsTextItem(f"{key1} / {key2} pour annuler")
        hint.setFont(get_font0(size=4))
        hint.setDefaultTextColor(QColor(120, 120, 140))
        hint.setZValue(Z_SCREEN + 2)
        tw = hint.boundingRect().width()
        hint.setPos((self.scene_w - tw) / 2, self._panel_y() + int(settings.tile_size * 10))
        self._items.append(hint)

    def _panel_x(self):
        return (self.scene_w - _PANEL_W_TILES * settings.tile_size) // 2

    def _panel_y(self):
        return (self.scene_h - _PANEL_H_TILES * settings.tile_size) // 2

    def _refresh_all(self):
        for i, row in enumerate(self._rows):
            row.set_selected(i == self._selected)
        is_on_btn = (self._selected == len(self._rows))
        self._apply_btn.set_state("selected" if is_on_btn else "normal")

    def key_press(self, key):
        if key in (settings.keys["PAUSE"], settings.keys["LEAVE"]):
            self._cancel()
        elif key == settings.keys["UP"]:
            self._nav(-1)
        elif key == settings.keys["DOWN"]:
            self._nav(+1)
        elif key == settings.keys["LEFT"]:
            self._cycle(-1)
        elif key == settings.keys["RIGHT"]:
            self._cycle(+1)
        elif key in (settings.keys["ATTACK"], settings.keys["INTERACT"], settings.keys["CONFIRM"]):
            self._press_current()

    def key_release(self, key):
        if key in (settings.keys["ATTACK"], settings.keys["INTERACT"], settings.keys["CONFIRM"]):
            self._release_current()

    def _nav(self, direction):
        old = self._selected
        self._selected = (self._selected + direction) % self._nav_count
        if self._selected != old:
            self._refresh_all()
            self._play_sfx("snd_choice")

    def _cycle(self, direction):
        if self._selected < len(self._rows):
            # empeche le cycle si non allowed (vient pas de l'ecran titre)
            if self._selected == 0 and not self._rescale_allowed:
                self._play_sfx("snd_false")
                return
            
            changed = self._rows[self._selected].handle_left_right(direction)
            if changed:
                self._play_sfx("snd_choice")

    def _press_current(self):
        if self._selected < len(self._rows):
            changed = self._rows[self._selected].handle_confirm()
            if changed:
                self._play_sfx("snd_choice")
        else:
            self._apply_btn.set_state("pressed")
            self._is_pressed = True

    def _release_current(self):
        if hasattr(self, '_is_pressed') and self._is_pressed:
            self._is_pressed = False
            self._apply_btn.set_state("selected")
            self._apply()
            

    def mouse_press(self, scene_pos):
        for i, row in enumerate(self._rows):
            px = self._panel_x()
            rect = QRectF(px, row.y, _PANEL_W_TILES * settings.tile_size, row.height)
            
            if rect.contains(scene_pos):
                if i == 0 and not self._rescale_allowed:
                    self._play_sfx("snd_false")
                    return
                self._selected = i
                self._refresh_all()

                if isinstance(row, TextChoiceRow):
                    # creation des zones de clics (2.5 tile a gauche et a droite du centre)
                    left_zone  = QRectF(row.x_center_val - 2.5 * settings.tile_size, row.y, 2.5 * settings.tile_size, row.height)
                    right_zone = QRectF(row.x_center_val, row.y, 2.5 * settings.tile_size, row.height)

                    if left_zone.contains(scene_pos):
                        if row.handle_left_right(-1):
                            self._play_sfx("snd_choice")
                            
                    elif right_zone.contains(scene_pos):
                        if row.handle_left_right(+1):
                            self._play_sfx("snd_choice")
                            
                    else:
                        changed = row.handle_confirm()
                        if changed:
                            self._play_sfx("snd_choice")
                            
                else:
                    changed = row.handle_confirm()
                    if changed:
                        self._play_sfx("snd_choice")
                return

        # clic sur le bouton Appliquer
        if self._apply_btn.contains(scene_pos):
            self._selected = len(self._rows)
            self._refresh_all()
            self._apply_btn.set_state("pressed")
            self._apply()
            
    def _apply(self):
        self._play_sfx("snd_accept")
        # extraction des valeurs depuis les lignes de l'interface
        res_idx = self._rows[0].index
        new_scale = _RESOLUTION_OPTIONS[res_idx][1]
        
        new_ctrl = _CONTROL_OPTIONS[self._rows[1].index][1]
        new_mus  = _VOLUME_OPTIONS[self._rows[2].index][1]
        new_sfx  = _VOLUME_OPTIONS[self._rows[3].index][1]
        new_crt  = self._rows[4].checked

        # verification de changement de scale
        needs_rebuild = (new_scale != settings.scale)

        # mise à jour de l'objet Settings global
        settings.resolution_index = res_idx
        settings.scale = new_scale
        settings.control_scheme = new_ctrl
        settings.music_volume = new_mus
        settings.sfx_volume = new_sfx
        settings.crt_overlay = new_crt

        # sauvegarde physique dans settings.json
        settings.save()

        # application immediates des parametres "Soft" (son + crt)
        self._apply_audio()
        self.screen_manager.apply_crt() 

        # aApplication du "Hard" Reboot si la résolution a change
        if needs_rebuild:
            self.screen_manager.rebuild_display()
            
    def _apply_audio(self):
        """
        met à jour les volumes sans redemarrer le jeu
        """
        self.screen_manager.music_manager.set_volume(settings.music_volume)
        
        if self.screen_manager.scene and hasattr(self.screen_manager.scene, 'sfx_manager'):
            self.screen_manager.scene.sfx_manager.set_volume(settings.sfx_volume)
            
    def _cancel(self):
        self._play_sfx("snd_reject")
        self.screen_manager.back_from_settings()