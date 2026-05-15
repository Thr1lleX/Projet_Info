# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
"""
Gestion du HUD (barre d'interface du haut).
Affiche les points de vie (coeurs) et les slots d'items.

Pour ajouter un element au HUD a l'avenir :
  1. Creer les QGraphicsItems dans une methode _build_xxx()
  2. Les ajouter a self._items via self._items.extend(...)
  3. Appeler _build_xxx() depuis __init__
"""

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt
from game.player import Player

from game.config import (
    TILE_SIZE, GRID_WIDTH, HUD_HEIGHT,
    HUD_HEART_FULL_PATH, HUD_HEART_HALF_FULL_PATH, HUD_HEART_EMPTY_PATH, HUD_ITEM_SLOT_PATH,
    Z_HUD, SCALE
)





# --- constantes visuelles du HUD (ajustables sans toucher a la logique) ---
HEART_SIZE        = int(TILE_SIZE * 0.90)   # 38px a SCALE=4
SLOT_SIZE         = int(TILE_SIZE * 0.90)
SPACING           = 6                        # pixels entre chaque icone
HEART_MARGIN_LEFT = 16
SLOT_MARGIN_RIGHT = 16

_HUD_W = GRID_WIDTH * TILE_SIZE             # 1024px
_HUD_H = HUD_HEIGHT * TILE_SIZE             # 128px


 # contantes zone de gauche  :

_MAX_HEARTS       = 6
HEART_MARGIN_LEFT = 16
HEART_MARGIN_TOP  = 8

MANA_BAR_W        = _MAX_HEARTS * (HEART_SIZE + SPACING) - SPACING  # meme largeur que la rangee de coeurs
MANA_BAR_H        = int(TILE_SIZE * 0.25)
MANA_MARGIN_TOP   = 6

# constantes zone centre

_BOX_SIZE         = int(TILE_SIZE * 1.3)   # taille d'une case (arme ou item)
_BOX_GAP          = int(TILE_SIZE * 0.5)   # espace entre les 2 cases
_CENTER_X         = _HUD_W // 2   + _HUD_W // 8 


_WEAPON_BOX_X     = _CENTER_X - _BOX_SIZE - _BOX_GAP // 2
_ITEM_BOX_X       = _CENTER_X + _BOX_GAP // 2
_BOX_Y            = (_HUD_H - _BOX_SIZE) // 2 - 6 

# constantes zone droite

_MINI_ICON_SIZE   = int(TILE_SIZE * 0.6)
_MINI_SPACING_X   = int(TILE_SIZE * 1.4)   # espace horizontal entre 2 colonnes (icone + "xN")
_MINI_SPACING_Y   = 4
_MINI_MARGIN_RIGHT = 16
_MINI_COLS        = 2
_MINI_ROWS        = 2

class HUD:
    """
    Gere tous les elements visuels de la barre du haut.
    Instancie les QGraphicsItems et les ajoute directement a la scene.
    Les items sont recuperables via get_items() pour les rendre persistants.
    """

    def __init__(self, scene, screen_manager):
        self.screen_manager = screen_manager
        self._items = []
        self._heart_triples = []

        #mana

        self._mana_bar_fill = None
        self._mana_max = 10

        # arme et item

        self._weapon_icon = None
        self._item_icon = None

        # partie droite

        self._mini_entries = []

        # cache pour aviter redessiner chaque frame

        self._current_pv = -1
        self._current_pv_max = -1
        self._last_dirty_state = True

        self._build_background(scene)
        self._build_hearts(scene, _MAX_HEARTS)
        self._build_mana_bar(scene)
        self._build_weapon_box(scene)
        self._build_item_box(scene)
        self._build_mini_inventory(scene)


    def _build_background(self, scene):
        bg = QGraphicsRectItem(0, 0, _HUD_W, _HUD_H)
        bg.setBrush(QBrush(QColor(0, 0, 0)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_HUD)
        scene.addItem(bg)
        self._items.append(bg)

    def _build_hearts(self, scene, _MAX_HEARTS):
        """Cree les paires d'icones (plein / vide) pour chaque slot de vie."""
        cy = HEART_MARGIN_TOP

        for i in range(_MAX_HEARTS):
            x = HEART_MARGIN_LEFT + i * (HEART_SIZE + SPACING)

            full_item  = self._make_heart_item(x, cy, state="full")
            half_item  = self._make_heart_item(x, cy, state="half")
            empty_item = self._make_heart_item(x, cy, state="empty")

            for item in (full_item, half_item, empty_item):
                item.setZValue(Z_HUD + 1)
                scene.addItem(item)
                self._items.append(item)

            self._heart_triples.append((full_item, half_item, empty_item))

        self._apply_heart_display(_MAX_HEARTS, _MAX_HEARTS)
        self._current_pv     = _MAX_HEARTS
        self._current_pv_max = _MAX_HEARTS

    def _make_heart_item(self, x, y, state):
        """
        Retourne un QGraphicsItem representant un coeur.
        Utilise le sprite si disponible, sinon un rectangle de couleur en placeholder.
        Sprites attendus : assets/hud/heart_full.png et assets/hud/heart_empty.png
        """
        if state == "full":
            path = HUD_HEART_FULL_PATH
        elif state == "half":
            path = HUD_HEART_HALF_FULL_PATH
        else:
            path = HUD_HEART_EMPTY_PATH

        pix  = QPixmap(path)

        if not pix.isNull():
            item = QGraphicsPixmapItem(
                pix.scaled(HEART_SIZE, HEART_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
        # backup si pas d'assets
        else:
            item = QGraphicsRectItem(0, 0, HEART_SIZE, HEART_SIZE)
            color = {
            "full": QColor(210, 30, 30),
            "half": QColor(210, 120, 120),
            "empty": QColor(55, 10, 10)
            } [state]
            item.setBrush(QBrush(color))
            item.setPen(QPen(Qt.NoPen))

        item.setPos(x, y)
        return item

    def _build_mana_bar(self, scene):
        from game.fonts import get_font0
        label = QGraphicsTextItem("Mana")
        label.setFont(get_font0(size = 3))
        label.setDefaultTextColor(QColor(100, 180, 255))
        label.setZValue(Z_HUD + 1)
        mana_y = HEART_MARGIN_TOP + HEART_SIZE + MANA_MARGIN_TOP
        label.setPos(HEART_MARGIN_LEFT, mana_y)
        scene.addItem(label)
        self._items.append(label)

        bar_y = mana_y + label.boundingRect().height() + 2

        # fond gris

        bg = QGraphicsRectItem(HEART_MARGIN_LEFT, bar_y, MANA_BAR_W, MANA_BAR_H)
        bg.setBrush(QBrush(QColor(30, 30, 50)))
        bg.setPen(QPen(QColor(60, 60, 100), 1))
        bg.setZValue(Z_HUD + 1)
        scene.addItem(bg)
        self._items.append(bg)

        # remplissage bleu

        self._mana_bar_fill = QGraphicsRectItem(HEART_MARGIN_LEFT, bar_y, 0, MANA_BAR_H)
        self._mana_bar_fill.setBrush(QBrush(QColor(50, 150, 255)))
        self._mana_bar_fill.setPen(QPen(Qt.NoPen))
        self._mana_bar_fill.setZValue(Z_HUD + 2)
        scene.addItem(self._mana_bar_fill)
        self._items.append(self._mana_bar_fill)
        self._mana_bar_y = bar_y

    def _build_weapon_box(self,scene):
        from game.fonts import get_font0

        slot_pix = QPixmap("assets/hud/item_slot.png").scaled(
        _BOX_SIZE, _BOX_SIZE, Qt.IgnoreAspectRatio, Qt.FastTransformation
        )

        # fond case

        box = QGraphicsPixmapItem(slot_pix)
        box.setPos(_WEAPON_BOX_X, _BOX_Y)
        box.setZValue(Z_HUD + 1)
        scene.addItem(box)
        self._items.append(box)

        # icone d'arme

        self._weapon_icon = QGraphicsPixmapItem()
        self._weapon_icon.setPos(_WEAPON_BOX_X + 4, _BOX_Y + 4)
        self._weapon_icon.setZValue(Z_HUD + 2)
        scene.addItem(self._weapon_icon)
        self._items.append(self._weapon_icon)


        # touche W

        key_label = QGraphicsTextItem("W")
        key_label.setFont(get_font0(size=3))
        key_label.setDefaultTextColor(QColor(150, 150, 150))
        key_label.setZValue(Z_HUD + 1)
        key_label.setPos(_WEAPON_BOX_X + _BOX_SIZE - 4, _BOX_Y + _BOX_SIZE + 2)
        scene.addItem(key_label)
        self._items.append(key_label)

    def _build_item_box(self, scene): # meme construction que weapon box
        from game.fonts import get_font0

        # fond case

        slot_pix = QPixmap("assets/hud/item_slot.png").scaled(
        _BOX_SIZE, _BOX_SIZE, Qt.IgnoreAspectRatio, Qt.FastTransformation
        )


        box = QGraphicsPixmapItem(slot_pix)
        box.setPos(_ITEM_BOX_X, _BOX_Y)
        box.setZValue(Z_HUD + 1)
        scene.addItem(box)
        self._items.append(box)

        # icone d'arme

        self._item_icon = QGraphicsPixmapItem()
        self._item_icon.setPos(_ITEM_BOX_X + 4, _BOX_Y + 4)
        self._item_icon.setZValue(Z_HUD + 2)
        scene.addItem(self._item_icon)
        self._items.append(self._item_icon)


        # touche X

        key_label = QGraphicsTextItem("X")
        key_label.setFont(get_font0(size=3))
        key_label.setDefaultTextColor(QColor(150, 150, 150))
        key_label.setZValue(Z_HUD + 1)
        key_label.setPos(_ITEM_BOX_X + _BOX_SIZE - 4, _BOX_Y + _BOX_SIZE + 2)
        scene.addItem(key_label)
        self._items.append(key_label)

    
    

    def _build_mini_inventory(self, scene):
        from game.fonts import get_font0
        from game.item_registry import get_item_data
        _MINI_ITEMS = ["pomme", "bombe", "potion", "key"]

        self._mini_entries = []

        # calcul position de depart à droite

        total_w = _MINI_COLS * _MINI_SPACING_X
        x_start = _HUD_W - _MINI_MARGIN_RIGHT - total_w
        y_start = (_HUD_H - (_MINI_ROWS * (_MINI_ICON_SIZE + _MINI_SPACING_Y) - _MINI_SPACING_Y)) // 2


        for idx, item_id in enumerate(_MINI_ITEMS):
            col = idx % _MINI_COLS
            row = idx // _MINI_COLS

            x = x_start + col * _MINI_SPACING_X
            y = y_start + row * (_MINI_ICON_SIZE + _MINI_SPACING_Y)

            # fond du mini-slot
            bg = QGraphicsRectItem(x, y, _MINI_ICON_SIZE, _MINI_ICON_SIZE)
            bg.setBrush(QBrush(QColor(25, 25, 50)))
            bg.setPen(QPen(QColor(80, 150, 220), 1))
            bg.setZValue(Z_HUD + 1)
            scene.addItem(bg)
            self._items.append(bg)

            # icone de l'item (chargee depuis le catalogue)
            data = get_item_data(item_id)
            pix = QPixmap(data["icon_path"])
            icon = QGraphicsPixmapItem(
                pix.scaled(_MINI_ICON_SIZE, _MINI_ICON_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
            icon.setPos(x, y)
            icon.setZValue(Z_HUD + 2)
            scene.addItem(icon)
            self._items.append(icon)


            # texte quantite "xN"
            count_text = QGraphicsTextItem("x0")
            count_text.setFont(get_font0(size=3))
            count_text.setDefaultTextColor(QColor(220, 220, 220))
            count_text.setZValue(Z_HUD + 2)
            count_text.setPos(x + _MINI_ICON_SIZE + 2, y)
            scene.addItem(count_text)
            self._items.append(count_text)

            self._mini_entries.append({
                "item_id": item_id,
                "text": count_text
            })           





    # ------------------------------------------------------------------
    # mise a jour
    # ------------------------------------------------------------------

    def update_hearts(self, pv, pv_max):
        """
        Met a jour l'affichage des coeurs.
        Appele chaque frame depuis game_loop ; ne fait rien si les PV n'ont pas change.
        """
        if pv == self._current_pv and pv_max == self._current_pv_max:
            return
        self._current_pv     = pv
        self._current_pv_max = pv_max
        self._apply_heart_display(pv, pv_max)

    def _apply_heart_display(self, pv, pv_max):
        for i, (full, half, empty) in enumerate(self._heart_triples):
            heart_value = pv-i
            if heart_value >= 1:
                full.show()
                half.hide()
                empty.hide()
            elif heart_value == 0.5:
                full.hide()
                half.show()
                empty.hide()
            else:
                full.hide()
                half.hide()
                empty.show()

 

    
    def update_hud(self, inventory, flags=None):
        # Appele chaque frame depuis game_loop, ne redessine que si dirty.

        if not inventory.is_dirty() and not self._last_dirty_state:
            return

        self._last_dirty_state = inventory.is_dirty()
        inventory.clear_dirty()

        # upgrade sword
        sword_path = "assets/items/sword.png"
        if flags and flags.get("sword_upgrade"):
            sword_path = "assets/items/sword_upgrade.png"
        pix = QPixmap(sword_path)
        if not pix.isNull():
            icon_size = _BOX_SIZE - 8
            self._weapon_icon.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.FastTransformation))

        # item equipe

        if self._item_icon is None:
            return

        equipped_id = inventory._equipped_item_id
        count = inventory.count_item(equipped_id) if equipped_id else 0
        if equipped_id is not None and count >0:
            from game.item_registry import get_item_data
            data = get_item_data(equipped_id)
            if data:
                pix = QPixmap(data["icon_path"])
                if not pix.isNull():
                    icon_size = _BOX_SIZE - 8
                    self._item_icon.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.FastTransformation))
                else:
                    self._item_icon.setPixmap(QPixmap())
            else:
                self._item_icon.setPixmap(QPixmap())
        else:
            self._item_icon.setPixmap(QPixmap())   # vide si rien d'equipe

        # quantites mini inv

        for entry in self._mini_entries:
            count = inventory.count_item(entry["item_id"])
            entry["text"].setPlainText(f"x{count}")

        # mana

        mana_count = inventory.count_item("mana")
        ratio = min(mana_count / max(self._mana_max, 1), 1.0)
        fill_w = int(MANA_BAR_W * ratio)
        self._mana_bar_fill.setRect(HEART_MARGIN_LEFT, self._mana_bar_y, fill_w, MANA_BAR_H)
            



    # ------------------------------------------------------------------
    # utilitaire
    # ------------------------------------------------------------------

    def get_items(self):
        """
        Retourne tous les QGraphicsItems du HUD.
        A passer a persistent_items de GameScene pour qu'ils survivent aux changements de salle.
        """
        return list(self._items)
