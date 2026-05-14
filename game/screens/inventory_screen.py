# # -*- coding: utf-8 -*-
# """
# Ecran d'inventaire (Tab pour ouvrir/fermer).

# Affiche une grille 5x6 = 30 slots.
#   - Rangee 0 (en haut) : slots actifs HUD (visuellement distincte).
#   - Rangees 1-4        : stockage etendu.

# Les icones sont lues depuis sm.inventory au moment du show().
# Le drag-and-drop est prevu : les methodes _on_slot_drag et _on_slot_drop
# sont des hooks vides a implementer ulterieurement.

# Navigation : Tab ou Echap pour fermer.
# """

# from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
# from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QKeySequence
# from PyQt5.QtCore import Qt, QRectF

# from game.screens.base_screen import BaseScreen
# from game.config import GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE, Z_SCREEN, KEYS, SCALE
# from game.fonts import get_font0

# _SCENE_W = GRID_WIDTH * TILE_SIZE
# _SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

# # --- geometrie du panneau ---
# _SLOT_SIZE    = 52
# _SLOT_SPACING = 8
# _COLS         = 6
# _ROWS         = 5
# _HUD_EXTRA_GAP = 14   # espace supplementaire entre rangee HUD et le reste

# _GRID_W = _COLS * (_SLOT_SIZE + _SLOT_SPACING) - _SLOT_SPACING  # 352
# _GRID_H = (_ROWS * (_SLOT_SIZE + _SLOT_SPACING) - _SLOT_SPACING
#            + _HUD_EXTRA_GAP)                                      # 306

# _PANEL_PAD = 22
# _TITLE_H   = 50
# _HINT_H    = 28
# _PANEL_W   = _GRID_W + 2 * _PANEL_PAD         # 396
# _PANEL_H   = _TITLE_H + _GRID_H + _HINT_H + 2 * _PANEL_PAD  # 428

# _PANEL_X   = (_SCENE_W - _PANEL_W) // 2
# _PANEL_Y   = (_SCENE_H - _PANEL_H) // 2

# _GRID_X    = _PANEL_X + _PANEL_PAD
# _GRID_Y    = _PANEL_Y + _PANEL_PAD + _TITLE_H

# # --- couleurs ---
# _C_OVERLAY    = QColor(0,  0,  0,  170)
# _C_PANEL_BG   = QColor(18, 18, 36, 250)
# _C_PANEL_BRD  = QColor(70, 70, 110)
# _C_SLOT_HUD   = QColor(40, 40, 80,  230)
# _C_SLOT_BRD_H = QColor(100, 100, 180)
# _C_SLOT_STD   = QColor(28, 28, 55,  230)
# _C_SLOT_BRD_S = QColor(60,  60,  100)
# _C_TITLE      = QColor(180, 180, 255)
# _C_HINT       = QColor(90,  90,  130)


# def _slot_row_y(row):
#     """Calcule la position Y du haut d'une rangee (avec gap apres rangee 0)."""
#     if row == 0:
#         return _GRID_Y
#     return _GRID_Y + (_SLOT_SIZE + _SLOT_SPACING) + _HUD_EXTRA_GAP + (row - 1) * (_SLOT_SIZE + _SLOT_SPACING)


# class InventoryScreen(BaseScreen):
#     """Ecran d'inventaire avec grille 5x6 de slots."""

#     def __init__(self, screen_manager):
#         super().__init__(screen_manager)
#         self._slot_bg_rects = []    # QGraphicsRectItem de fond pour chaque slot
#         self._icon_items    = [None] * 30   # QGraphicsPixmapItem d'icone par slot
#         self._slot_positions = []   # (x, y) de chaque slot (calcule en _build)
#         self._cursor = 0              # index du slot selectionne
#         self._equip_marker = None     # QGraphicsItem pour le marqueur "equipe"
#         self._info_text = None        # QGraphicsTextItem pour nom + quantite
#     # ------------------------------------------------------------------
#     # cycle de vie (surcharge pour gerer les icones hors self._items)
#     # ------------------------------------------------------------------

#     def show(self, scene):
#         super().show(scene)
#         self._refresh_icons(scene)
#         self._refresh_cursor()            # ← surbrillance du slot actuel
#         self._refresh_equip_marker(scene) # ← marqueur vert sur item equipe

#     def hide(self):
#         for icon in self._icon_items:
#             if icon is not None:
#                 s = icon.scene()
#                 if s:
#                     s.removeItem(icon)
#         super().hide()

#     # ------------------------------------------------------------------
#     # construction
#     # ------------------------------------------------------------------

#     def _build(self):
#         self._build_overlay()
#         self._build_panel()
#         self._build_title()
#         self._build_slots()
#         self._build_info_text()    # ← NOUVEAU
#         self._build_hint()
#         self._refresh_cursor()     # ← NOUVEAU (met la surbrillance initiale)

#     def _build_overlay(self):
#         overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
#         overlay.setBrush(QBrush(_C_OVERLAY))
#         overlay.setPen(QPen(Qt.NoPen))
#         overlay.setZValue(Z_SCREEN)
#         self._items.append(overlay)

#     def _build_panel(self):
#         panel = QGraphicsRectItem(_PANEL_X, _PANEL_Y, _PANEL_W, _PANEL_H)
#         panel.setBrush(QBrush(_C_PANEL_BG))
#         panel.setPen(QPen(_C_PANEL_BRD, 2))
#         panel.setZValue(Z_SCREEN + 1)
#         self._items.append(panel)

#     def _build_title(self):
#         title = QGraphicsTextItem("Inventaire")
#         title.setFont(get_font0(size=10))
#         title.setDefaultTextColor(_C_TITLE)
#         title.setZValue(Z_SCREEN + 2)
#         tw = title.boundingRect().width()
#         title.setPos((_SCENE_W - tw) / 2, _PANEL_Y + _PANEL_PAD)
#         self._items.append(title)

#     def _build_slots(self):
#         self._slot_bg_rects = []
#         self._slot_positions = []
#         for i in range(30):
#             col = i % _COLS
#             row = i // _COLS
#             x = _GRID_X + col * (_SLOT_SIZE + _SLOT_SPACING)
#             y = _slot_row_y(row)
#             self._slot_positions.append((x, y))

#             is_hud = (row == 0)
#             bg_color  = _C_SLOT_HUD  if is_hud else _C_SLOT_STD
#             brd_color = _C_SLOT_BRD_H if is_hud else _C_SLOT_BRD_S

#             rect = QGraphicsRectItem(x, y, _SLOT_SIZE, _SLOT_SIZE)
#             rect.setBrush(QBrush(bg_color))
#             rect.setPen(QPen(brd_color, 1))
#             rect.setZValue(Z_SCREEN + 2)
#             self._items.append(rect)
#             self._slot_bg_rects.append(rect)

#     def _build_hint(self):
#         key1 = QKeySequence(KEYS["LEAVE"]).toString()
#         key2 = QKeySequence(KEYS["INVENTORY"]).toString()
#         key3 = QKeySequence(KEYS["PAUSE"]).toString()
#         hint = QGraphicsTextItem(f"{key1} / {key2} / {key3} pour fermer")
#         hint.setFont(get_font0(size=4))
#         hint.setDefaultTextColor(_C_HINT)
#         hint.setZValue(Z_SCREEN + 2)
#         hw = hint.boundingRect().width()
#         hint.setPos((_SCENE_W - hw) / 2, _PANEL_Y + _PANEL_H - _PANEL_PAD - _HINT_H + 6)
#         self._items.append(hint)
    
#     def _build_info_text(self):
#         """
#         Texte sous la grille qui affiche le nom et la quantite 
#         de l'item sous le curseur.
#         """
#         self._info_text = QGraphicsTextItem("")
#         self._info_text.setFont(get_font0(size=5))
#         self._info_text.setDefaultTextColor(QColor(200, 200, 230))
#         self._info_text.setZValue(Z_SCREEN + 2)

#         # position : centre horizontal, juste sous le dernier rang de slots
#         last_row_y = _slot_row_y(_ROWS - 1)
#         text_y = last_row_y + _SLOT_SIZE + 10

#         self._info_text.setPos(_GRID_X, text_y)
#         self._items.append(self._info_text)

#     # ------------------------------------------------------------------
#     # mise a jour des icones
#     # ------------------------------------------------------------------

#     def _refresh_icons(self, scene):
#         """Relit l'inventaire et (re)affiche les icones dans les slots."""
#         # suppression des anciennes icones
#         for i, icon in enumerate(self._icon_items):
#             if icon is not None:
#                 s = icon.scene()
#                 if s:
#                     s.removeItem(icon)
#                 self._icon_items[i] = None

#         inventory = getattr(self.screen_manager, 'inventory', None)
#         if inventory is None:
#             return

#         for i in range(30):
#             slot = inventory.get_slot(i)
#             if slot is None or slot.icon is None:
#                 continue
#             x, y = self._slot_positions[i]
#             icon_item = QGraphicsPixmapItem(
#                 slot.icon.scaled(
#                     _SLOT_SIZE, _SLOT_SIZE,
#                     Qt.KeepAspectRatio, Qt.FastTransformation
#                 )
#             )
#             icon_item.setPos(x, y)
#             icon_item.setZValue(Z_SCREEN + 3)
#             scene.addItem(icon_item)
#             self._icon_items[i] = icon_item

#     # ------------------------------------------------------------------
#     # evenements
#     # ------------------------------------------------------------------

#     def key_press(self, key):
#         if key in (KEYS["LEAVE"], KEYS["INVENTORY"],KEYS["PAUSE"]):
#             self.screen_manager.close_inventory()
#         elif key == KEYS["UP"]:
#             self._move_cursor(0, -1)
#         elif key == KEYS["DOWN"]:
#             self._move_cursor(0, +1)
#         elif key == KEYS["LEFT"]:
#             self._move_cursor(-1, 0)
#         elif key == KEYS["RIGHT"]:
#             self._move_cursor(+1, 0)
#         elif key in (KEYS["INTERACT"], KEYS["CONFIRM"]):
#             self._equip_selected()

#     def _move_cursor(self, dx, dy):
#         col = self._cursor % _COLS
#         row = self._cursor // _COLS
#         col = (col + dx) % _COLS
#         row = (row + dy) % _ROWS
#         self._cursor = row * _COLS + col
#         self._refresh_cursor()
#         self._play_sfx("snd_choice")

#     def _refresh_cursor(self):
#         for i, rect in enumerate(self._slot_bg_rects):
#             row = i // _COLS
#             is_hud = (row == 0)
#             rect.setPen(QPen(_C_SLOT_BRD_H if is_hud else _C_SLOT_BRD_S, 1))
#         # curseur = bordure jaune epaisse
#         self._slot_bg_rects[self._cursor].setPen(QPen(QColor(255, 220, 50), 3))
#         # mettre a jour le texte d'info
#         self._update_info_text()

#     def _equip_selected(self):
#         inventory = self.screen_manager.inventory
#         slot = inventory.get_slot(self._cursor)
#         if slot is None:
#             self._play_sfx("snd_reject")
#             return
#         if slot.category not in ("consumable", "permanent"):
#             self._play_sfx("snd_reject")
#             return
#         inventory.equip_item(slot.item_id)
#         self._play_sfx("snd_accept")
#         self._refresh_equip_marker()
        
#     def _update_info_text(self):
#         if self._info_text is None:
#             return
#         inventory = self.screen_manager.inventory
#         slot = inventory.get_slot(self._cursor)
#         if slot is None:
#             self._info_text.setPlainText("")
#         elif slot.category == "consumable":
#             self._info_text.setPlainText(f"{slot.name}  x{slot.count}")
#         else:
#             self._info_text.setPlainText(f"{slot.name}")

#     def _refresh_equip_marker(self, scene=None):
#         """
#         Place (ou deplace) le marqueur vert sur le slot 
#         qui contient l'item actuellement equipe en consommable.
#         """
#         inventory = self.screen_manager.inventory
#         equipped_id = inventory._equipped_item_id

#         # --- Cas 1 : rien d'equipe → cacher le marqueur ---
#         if equipped_id is None:
#             if self._equip_marker is not None:
#                 self._equip_marker.setVisible(False)
#             return

#         # --- Trouver le premier slot qui contient cet item ---
#         target_index = None
#         for i in range(inventory.total_slots):
#             slot = inventory.get_slot(i)
#             if slot is not None and slot.item_id == equipped_id:
#                 target_index = i
#                 break

#         if target_index is None:
#             # l'item equipe n'est plus en stock
#             if self._equip_marker is not None:
#                 self._equip_marker.setVisible(False)
#             return

#         # --- Positionner le marqueur ---
#         x, y = self._slot_positions[target_index]

#         if self._equip_marker is None:
#             # creation du marqueur (un petit carre vert en haut a droite du slot)
#             marker_size = 12
#             self._equip_marker = QGraphicsRectItem(0, 0, marker_size, marker_size)
#             self._equip_marker.setBrush(QBrush(QColor(50, 220, 80)))
#             self._equip_marker.setPen(QPen(Qt.NoPen))
#             self._equip_marker.setZValue(Z_SCREEN + 4)
#             # on l'ajoute a self._items pour que show/hide le gere
#             self._items.append(self._equip_marker)
#             # si on est deja dans une scene, l'ajouter aussi
#             if scene is not None:
#                 scene.addItem(self._equip_marker)

#         # placer en haut a droite du slot
#         marker_size = 12
#         self._equip_marker.setPos(x + _SLOT_SIZE - marker_size - 2, y + 2)
#         self._equip_marker.setVisible(True)
#     # ------------------------------------------------------------------
#     # hooks drag-and-drop (a implementer ulterieurement)
#     # ------------------------------------------------------------------

#     def _on_slot_click(self, slot_index, scene_pos):
#         """Appele lors d'un clic sur un slot. Point d'entree futur pour le drag-and-drop."""
#         pass

#     def _on_slot_drag(self, from_index):
#         """Demarre un drag depuis un slot. A implementer."""
#         pass

#     def _on_slot_drop(self, from_index, to_index):
#         """Depose un item sur un slot. A implementer."""
#         pass

# -*- coding: utf-8 -*-

# Auteur : essentiellement Mateo

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QKeySequence
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE, Z_SCREEN, KEYS, SCALE
from game.fonts import get_font0

# --- Géométrie compacte ---
_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

_BASE_SLOT_PX = 32 
_SLOT_SIZE = _BASE_SLOT_PX * SCALE
_SLOT_SPACING = 2 * SCALE # Espacement réduit
_COLS = 6

_TOTAL_GRID_W = (_COLS * _SLOT_SIZE) + ((_COLS - 1) * _SLOT_SPACING)

# Fenêtre beaucoup plus compacte
_PANEL_PAD = 8 * SCALE
_PANEL_W = _TOTAL_GRID_W + (2 * _PANEL_PAD)
_PANEL_H = 100 * SCALE # Réduit de 160 à 100

_PANEL_X = (_SCENE_W - _PANEL_W) // 2
_PANEL_Y = (_SCENE_H - _PANEL_H) // 2

class InventoryScreen(BaseScreen):
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self._slot_positions = []
        self._icon_items = [None] * _COLS
        self._cursor = 0
        self._picker_item = None
        self._equip_marker = None
        self._info_text = None

    def _build(self):
        # Overlay Noir
        overlay = QGraphicsRectItem(0, 0, _SCENE_W, _SCENE_H)
        overlay.setBrush(QBrush(QColor(0, 0, 0, 180)))
        overlay.setPen(QPen(Qt.NoPen))
        overlay.setZValue(Z_SCREEN)
        self._items.append(overlay)

        # Panneau Bleu
        panel = QGraphicsRectItem(_PANEL_X, _PANEL_Y, _PANEL_W, _PANEL_H)
        panel.setBrush(QBrush(QColor(20, 30, 80, 240)))
        panel.setPen(QPen(QColor(100, 150, 255), 1 * SCALE))
        panel.setZValue(Z_SCREEN + 1)
        self._items.append(panel)

        # Titre
        title = QGraphicsTextItem("Inventaire")
        title.setFont(get_font0(size=10))
        title.setDefaultTextColor(QColor("white"))
        title.setZValue(Z_SCREEN + 2)
        tw = title.boundingRect().width()
        title.setPos((_SCENE_W - tw) / 2, _PANEL_Y + 5)
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
        self._info_text.setPos(_PANEL_X + _PANEL_PAD, _PANEL_Y + _PANEL_H - (30 * SCALE))
        self._items.append(self._info_text)

        # Aide
        key1 = QKeySequence(KEYS["INVENTORY"]).toString()
        key2 = QKeySequence(KEYS["LEAVE"]).toString()
        key3 = QKeySequence(KEYS["PAUSE"]).toString()
        hint = QGraphicsTextItem(f"{key1} / {key2} / {key3} pour fermer")
        hint.setFont(get_font0(size=5))
        hint.setDefaultTextColor(QColor(150, 150, 150))
        hint.setZValue(Z_SCREEN + 2)
        hw = hint.boundingRect().width()
        hint.setPos((_SCENE_W - hw) / 2, _PANEL_Y + _PANEL_H - (12 * SCALE))
        self._items.append(hint)

    def _build_slots(self):
        slot_pix = QPixmap("assets/hud/item_slot.png").scaled(
            int(_SLOT_SIZE), int(_SLOT_SIZE), Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        start_x = (_SCENE_W - _TOTAL_GRID_W) / 2
        slot_y = _PANEL_Y + (30 * SCALE)

        self._slot_positions = []
        for i in range(_COLS):
            x = start_x + (i * (_SLOT_SIZE + _SLOT_SPACING))
            slot_bg = QGraphicsPixmapItem(slot_pix)
            slot_bg.setPos(x, slot_y)
            slot_bg.setZValue(Z_SCREEN + 2)
            self._items.append(slot_bg)
            self._slot_positions.append((x, slot_y))

    def _build_picker(self):
        picker_pix = QPixmap("assets/hud/item_slot_picker.png").scaled(
            int(_SLOT_SIZE), int(_SLOT_SIZE), Qt.IgnoreAspectRatio, Qt.FastTransformation
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
                padding = 6 * SCALE
                icon_item = QGraphicsPixmapItem(
                    slot_data.icon.scaled(
                        int(_SLOT_SIZE - padding), int(_SLOT_SIZE - padding),
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
            self._info_text.setPos((_SCENE_W - tw) / 2, self._info_text.y())
        else:
            self._info_text.setPlainText("---")

    def key_press(self, key):
        if key in (KEYS["LEAVE"], KEYS["INVENTORY"], KEYS["PAUSE"]):
            self.screen_manager.close_inventory()
        elif key == KEYS["LEFT"]:
            self._move_cursor(-1)
        elif key == KEYS["RIGHT"]:
            self._move_cursor(1)
        elif key in (KEYS["INTERACT"], KEYS["CONFIRM"]):
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
            self._play_sfx("snd_reject")

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
            m_size = 6 * SCALE
            self._equip_marker = QGraphicsRectItem(0, 0, m_size, m_size)
            self._equip_marker.setBrush(QBrush(QColor(0, 255, 100)))
            self._equip_marker.setPen(QPen(Qt.NoPen))
            self._equip_marker.setZValue(Z_SCREEN + 6)
            self._items.append(self._equip_marker)
            if scene: scene.addItem(self._equip_marker)

        self._equip_marker.setPos(x + _SLOT_SIZE - (8 * SCALE), y + 2 * SCALE)
        self._equip_marker.setVisible(True)
