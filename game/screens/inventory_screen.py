# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QKeySequence
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import HUD_HEIGHT, Z_SCREEN
from game.fonts import get_font0

from game.settings import settings

# --- parametres de geometrie --

_BASE_SLOT_PX = 32 
_COLS = 6

class InventoryScreen(BaseScreen):
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._slot_positions = []
        self._icon_items = [None] * _COLS
        self._cursor = 0
        self._picker_item = None
        self._equip_marker = None
        self._info_text = None
    
    @property
    def slot_size(self):
        return _BASE_SLOT_PX * settings.scale
    
    @property
    def slot_spacing(self):
        return 2 * settings.scale
    
    @property
    def total_grid_w(self):
        return (_COLS * self.slot_size) + ((_COLS - 1) * self.slot_spacing)
    
    @property
    def panel_pad(self):
        return 8 * settings.scale
    
    @property
    def panel_w(self):
        return self.total_grid_w + (2 * self.panel_pad)
    
    @property
    def panel_h(self):
        return 100 * settings.scale
    
    @property
    def panel_x(self):
        return (self.scene_w - self.panel_w) // 2
    
    @property
    def panel_y(self):
        return (self.scene_h - self.panel_h) // 2
    

    def _build(self):
        # Overlay Noir
        overlay = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
        overlay.setBrush(QBrush(QColor(0, 0, 0, 180)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

        # Panneau Bleu
        panel = QGraphicsRectItem(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
        panel.setBrush(QBrush(QColor(20, 30, 80, 240)))
        panel.setPen(QPen(QColor(100, 150, 255), 1 * settings.scale))
        panel.setZValue(Z_SCREEN + 1)
        self._items.append(panel)

        # Titre
        title = QGraphicsTextItem("Inventaire")
        title.setFont(get_font0(size=10))
        title.setDefaultTextColor(QColor("white"))
        title.setZValue(Z_SCREEN + 2)
        tw = title.boundingRect().width()
        title.setPos((self.scene_w - tw) / 2, self.panel_y + 5)
        self._items.append(title)

        # Slots
        self._build_slots()

        # Picker
        self._build_picker()

        # Texte d'information (Nom)
        self._info_text = QGraphicsTextItem("")
        self._info_text.setFont(get_font0(size=7.5))
        self._info_text.setDefaultTextColor(QColor(255, 255, 100))
        self._info_text.setZValue(Z_SCREEN + 5)
        self._info_text.setPos(self.panel_x + self.panel_pad, self.panel_y + self.panel_h - (30 * settings.scale))
        self._items.append(self._info_text)

        # Aide
        key1 = QKeySequence(settings.keys["INVENTORY"]).toString()
        key2 = QKeySequence(settings.keys["LEAVE"]).toString()
        key3 = QKeySequence(settings.keys["PAUSE"]).toString()
        hint = QGraphicsTextItem(f"{key1} / {key2} / {key3} pour fermer")
        hint.setFont(get_font0(size=5))
        hint.setDefaultTextColor(QColor(150, 150, 150))
        hint.setZValue(Z_SCREEN + 2)
        hw = hint.boundingRect().width()
        hint.setPos((self.scene_w - hw) / 2, self.panel_y + self.panel_h - (12 * settings.scale))
        self._items.append(hint)

    def _build_slots(self):
        slot_pix = QPixmap("assets/hud/item_slot.png").scaled(
            int(self.slot_size), int(self.slot_size), Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        start_x = (self.scene_w - self.total_grid_w) / 2
        slot_y = self.panel_y + (30 * settings.scale)

        self._slot_positions = []
        for i in range(_COLS):
            x = start_x + (i * (self.slot_size + self.slot_spacing))
            slot_bg = QGraphicsPixmapItem(slot_pix)
            slot_bg.setPos(x, slot_y)
            slot_bg.setZValue(Z_SCREEN + 2)
            self._items.append(slot_bg)
            self._slot_positions.append((x, slot_y))

    def _build_picker(self):
        picker_pix = QPixmap("assets/hud/item_slot_picker.png").scaled(
            int(self.slot_size), int(self.slot_size), Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        self._picker_item = QGraphicsPixmapItem(picker_pix)
        self._picker_item.setZValue(Z_SCREEN + 10)
        self._items.append(self._picker_item)

    def show(self, scene):
        super().show(scene)
        self._refresh_icons(scene)
        self._refresh_cursor()
        self._refresh_equip_marker(scene)

    def hide(self):
        for icon in self._icon_items:
            if icon and icon.scene():
                icon.scene().removeItem(icon)
        super().hide()

    def _refresh_icons(self, scene):
        for i, icon in enumerate(self._icon_items):
            if icon and icon.scene():
                icon.scene().removeItem(icon)
            self._icon_items[i] = None

        inventory = self.screen_manager.inventory
        for i in range(_COLS):
            slot_data = inventory.get_slot(i)
            if slot_data and slot_data.icon:
                x, y = self._slot_positions[i]
                padding = 6 * settings.scale
                icon_item = QGraphicsPixmapItem(
                    slot_data.icon.scaled(
                        int(self.slot_size - padding), int(self.slot_size - padding),
                        Qt.KeepAspectRatio, Qt.FastTransformation
                    )
                )
                icon_item.setPos(x + padding/2, y + padding/2)
                icon_item.setZValue(Z_SCREEN + 4)
                scene.addItem(icon_item)
                self._icon_items[i] = icon_item

    def _refresh_cursor(self):
        x, y = self._slot_positions[self._cursor]
        self._picker_item.setPos(x, y)
        
        inventory = self.screen_manager.inventory
        slot_data = inventory.get_slot(self._cursor)
        
        if slot_data:
            text = f"{slot_data.name}"
            if slot_data.category == "consumable":
                text += f" x{slot_data.count}"
            self._info_text.setPlainText(text)
            tw = self._info_text.boundingRect().width()
            self._info_text.setPos((self.scene_w - tw) / 2, self._info_text.y())
        else:
            self._info_text.setPlainText("---")

    def key_press(self, key):
        if key in (settings.keys["LEAVE"], settings.keys["INVENTORY"], settings.keys["PAUSE"]):
            self.screen_manager.close_inventory()
        elif key == settings.keys["LEFT"]:
            self._move_cursor(-1)
        elif key == settings.keys["RIGHT"]:
            self._move_cursor(1)
        elif key in (settings.keys["INTERACT"], settings.keys["CONFIRM"]):
            self._equip_selected()

    def _move_cursor(self, dx):
        self._cursor = (self._cursor + dx) % _COLS
        self._refresh_cursor()
        self._play_sfx("snd_choice")

    def _equip_selected(self):
        inventory = self.screen_manager.inventory
        slot = inventory.get_slot(self._cursor)
        if slot and slot.category in ("consumable", "permanent"):
            inventory.equip_item(slot.item_id)
            self._play_sfx("snd_accept")
            self._refresh_equip_marker()
        else:
            self._play_sfx("snd_false")

    def _refresh_equip_marker(self, scene=None):
        inventory = self.screen_manager.inventory
        equipped_id = inventory._equipped_item_id

        if not equipped_id:
            if self._equip_marker: self._equip_marker.setVisible(False)
            return

        target_idx = None
        for i in range(_COLS):
            s = inventory.get_slot(i)
            if s and s.item_id == equipped_id:
                target_idx = i
                break

        if target_idx is None:
            if self._equip_marker: self._equip_marker.setVisible(False)
            return

        x, y = self._slot_positions[target_idx]
        
        if not self._equip_marker:
            m_size = 6 * settings.scale
            self._equip_marker = QGraphicsRectItem(0, 0, m_size, m_size)
            self._equip_marker.setBrush(QBrush(QColor(0, 255, 100)))
            self._equip_marker.setPen(QPen(Qt.NoPen))
            self._equip_marker.setZValue(Z_SCREEN + 6)
            self._items.append(self._equip_marker)
            if scene: scene.addItem(self._equip_marker)

        self._equip_marker.setPos(x + self.slot_size - (8 * settings.scale), y + 2 * settings.scale)
        self._equip_marker.setVisible(True)
