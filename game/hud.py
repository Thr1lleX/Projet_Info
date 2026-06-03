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
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap,  QKeySequence
from PyQt5.QtCore import Qt
from game.player import Player

from game.config import (
    GRID_WIDTH, HUD_HEIGHT, HUD_HEART_FULL_PATH, 
    HUD_HEART_HALF_FULL_PATH, HUD_HEART_EMPTY_PATH,Z_HUD
    )
from game.item_registry import get_item_data

from game.settings import settings

# constantes zone droite
_MINI_COLS = 2
_MINI_ROWS = 2

class HUD:
    """
    Gere tous les elements visuels de la barre du haut.
    Instancie les QGraphicsItems et les ajoute directement a la scene.
    Les items sont recuperables via get_items() pour les rendre persistants.
    """

    def __init__(self, scene, screen_manager):
        self.player = Player(settings.scale)
        self.screen_manager = screen_manager
        self._items = []
        self._heart_triples = []

        #mana

        self._mana_bar_fill = None
        self._mana_max = get_item_data("mana")["stack_max"]

        # arme et item

        self._weapon_icon = None
        self._item_icon = None

        # partie droite

        self._mini_entries = []

        # cache pour aviter redessiner chaque frame

        self._current_pv = -1
        self._current_pv_max = -1

        self._build_background(scene)
        self._build_hearts(scene, self.player._pv_max)
        self._build_mana_bar(scene)
        self._build_weapon_box(scene)
        self._build_item_box(scene)
        self._build_mini_inventory(scene)
    
    """
    DEFINITION DES CONSTANTES DE GEOMETRIE
    """
    # constantes visuelles du hud
    @property
    def heart_size(self):
        return int(settings.tile_size * 0.90)
    @property
    def slot_size(self):
        return int(settings.tile_size * 0.90)
    @property
    def spacing(self):
        return int(2 * settings.scale)
    @property
    def heart_margin_left(self):
        return 4 * settings.scale
    @property
    def slot_margin_right(self):
        return 4 * settings.scale
    @property
    def heart_margin_top(self):
        return 2 * settings.scale
    @property
    def _hud_w(self):
        return GRID_WIDTH * settings.tile_size
    @property
    def _hud_h(self):
        return HUD_HEIGHT * settings.tile_size
    
    # constantes zone de gauche
    @property
    def mana_bar_w(self):
        return self.player._pv_max * (self.heart_size + self.spacing) - self.spacing
    @property
    def mana_bar_h(self):
        return int(settings.tile_size * 0.25)
    @property
    def mana_margin_top(self):
        return 4 * settings.scale
    
    # constantes zone centre
    @property
    def _box_size(self):
        return int(settings.tile_size * 1.25)
    @property
    def _box_gap(self):
        return int(settings.tile_size * 0.5)
    @property
    def _center_x(self):
        return self._hud_w // 2 + self._hud_w // 16
    @property
    def _weapon_box_x(self):
        return self._center_x - self. _box_size - self._box_gap // 2
    @property
    def _item_box_x(self):
        return self._center_x + self._box_gap // 2
    @property
    def _box_y(self):
        return (self._hud_h - self._box_size) // 2 - 2 * settings.scale
    
    # constantes zone droite
    @property
    def _mini_icon_size(self):
        return int(settings.tile_size * 0.75)
    @property
    def _mini_spacing_x(self):
        return int(settings.tile_size *2)
    @property
    def _mini_spacing_y(self):
        return 1 * settings.scale
    @property
    def _mini_margin_right(self):
        return 2 * settings.scale

    """
    C'EST BON C'EST FINI
    """
    
    def _build_background(self, scene):
        bg = QGraphicsRectItem(0, 0, self._hud_w, self._hud_h)
        bg.setBrush(QBrush(QColor(0, 0, 0)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_HUD)
        scene.addItem(bg)
        self._items.append(bg)

    def _build_hearts(self, scene, pv_max):
        """Cree les paires d'icones (plein / vide) pour chaque slot de vie."""
        cy = self.heart_margin_top

        for i in range(pv_max):
            x = self.heart_margin_left + i * (self.heart_size + self.spacing)

            full_item  = self._make_heart_item(x, cy, state="full")
            half_item  = self._make_heart_item(x, cy, state="half")
            empty_item = self._make_heart_item(x, cy, state="empty")

            for item in (full_item, half_item, empty_item):
                item.setZValue(Z_HUD + 1)
                scene.addItem(item)
                self._items.append(item)

            self._heart_triples.append((full_item, half_item, empty_item))

        self._apply_heart_display(pv_max, pv_max)
        self._current_pv     = pv_max
        self._current_pv_max = pv_max

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
                pix.scaled(self.heart_size, self.heart_size, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
        # backup si pas d'assets
        else:
            item = QGraphicsRectItem(0, 0, self.heart_size, self.heart_size)
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
        
        bar_y = (self.heart_margin_top+ self.heart_size + self.mana_margin_top)
        # fond gris

        bg = QGraphicsRectItem(self.heart_margin_left, bar_y,  self.mana_bar_w, self.mana_bar_h)
        bg.setBrush(QBrush(QColor(30, 30, 50)))
        bg.setPen(QPen(QColor(60, 60, 100), 1))
        bg.setZValue(Z_HUD + 1)
        scene.addItem(bg)
        self._items.append(bg)

        # remplissage bleu

        self._mana_bar_fill = QGraphicsRectItem(self.heart_margin_left, bar_y, 0, self.mana_bar_h)
        self._mana_bar_fill.setBrush(QBrush(QColor(65, 97, 251)))
        self._mana_bar_fill.setPen(QPen(Qt.NoPen))
        self._mana_bar_fill.setZValue(Z_HUD + 2)
        scene.addItem(self._mana_bar_fill)
        self._items.append(self._mana_bar_fill)
        self._mana_bar_y = bar_y

    def _build_weapon_box(self,scene):
        from game.fonts import get_font0

        slot_pix = QPixmap("assets/hud/item_slot.png").scaled(
        self._box_size, self._box_size, Qt.IgnoreAspectRatio, Qt.FastTransformation
        )

        # fond case

        box = QGraphicsPixmapItem(slot_pix)
        box.setPos(self._weapon_box_x, self._box_y)
        box.setZValue(Z_HUD + 1)
        scene.addItem(box)
        self._items.append(box)

        # icone d'arme
        self.box_padding = 4 * settings.scale
        self._weapon_icon = QGraphicsPixmapItem()
        self._weapon_icon.setPos(self._weapon_box_x + self.box_padding / 2, self._box_y + self.box_padding / 2)
        self._weapon_icon.setZValue(Z_HUD + 2)
        scene.addItem(self._weapon_icon)
        self._items.append(self._weapon_icon)


        # touche d'attaque
        key = QKeySequence(settings.keys["ATTACK"]).toString()
        self._attack_key_label = QGraphicsTextItem(key)
        self._attack_key_label.setFont(get_font0(size=5))
        self._attack_key_label.setFont(get_font0(size=5))
        self._attack_key_label.setDefaultTextColor(QColor(150, 150, 150))
        self._attack_key_label.setZValue(Z_HUD + 1)
        self._attack_key_label.setPos(self._weapon_box_x + self._box_size, self._box_y + self._box_size -settings.scale*4)
        scene.addItem(self._attack_key_label)
        self._items.append(self._attack_key_label)

    def _build_item_box(self, scene): # meme construction que weapon box
        from game.fonts import get_font0

        # fond case
        slot_pix = QPixmap("assets/hud/item_slot.png").scaled(
        self._box_size, self._box_size, Qt.IgnoreAspectRatio, Qt.FastTransformation
        )


        box = QGraphicsPixmapItem(slot_pix)
        box.setPos(self._item_box_x, self._box_y)
        box.setZValue(Z_HUD + 1)
        scene.addItem(box)
        self._items.append(box)

        # icone d'item

        self._item_icon = QGraphicsPixmapItem()
        self._item_icon.setPos(self._item_box_x + self.box_padding / 2, self._box_y + self.box_padding / 2)
        self._item_icon.setZValue(Z_HUD + 2)
        scene.addItem(self._item_icon)
        self._items.append(self._item_icon)


        # touche d'item
        key = QKeySequence(settings.keys["ITEM"]).toString()
        self._item_key_label = QGraphicsTextItem(key)
        self._item_key_label.setFont(get_font0(size=5))
        self._item_key_label.setDefaultTextColor(QColor(150, 150, 150))
        self._item_key_label.setZValue(Z_HUD + 1)
        self._item_key_label.setPos(self._item_box_x + self._box_size,  self._box_y +  self._box_size-settings.scale*4)
        scene.addItem(self._item_key_label)
        self._items.append(self._item_key_label)
    

    def _build_mini_inventory(self, scene):
        from game.fonts import get_font0
        from game.item_registry import get_item_data
        _MINI_ITEMS = ["pomme", "bombe", "potion", "key"]

        self._mini_entries = []

        # calcul position de depart à droite

        total_w = _MINI_COLS * self._mini_spacing_x
        x_start = self._hud_w - self._mini_margin_right - total_w
        y_start = (self._hud_h - (_MINI_ROWS * (self._mini_icon_size + self._mini_spacing_y) - self._mini_spacing_y)) // 2


        for idx, item_id in enumerate(_MINI_ITEMS):
            col = idx % _MINI_COLS
            row = idx // _MINI_COLS

            x = x_start + col * self._mini_spacing_x
            y = y_start + row * (self._mini_icon_size + self._mini_spacing_y)

            # icone de l'item (chargee depuis le catalogue)
            data = get_item_data(item_id)
            pix = QPixmap(data["icon_path"])
            icon = QGraphicsPixmapItem(
                pix.scaled(self._mini_icon_size, self._mini_icon_size, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
            icon.setPos(x, y)
            icon.setZValue(Z_HUD + 2)
            scene.addItem(icon)
            self._items.append(icon)


            # texte quantite "xN"
            count_text = QGraphicsTextItem("x0")
            count_text.setFont(get_font0(size=5))
            count_text.setDefaultTextColor(QColor(220, 220, 220))
            count_text.setZValue(Z_HUD + 2)
            count_text.setPos(x + self._mini_icon_size + 2*settings.scale, y)
            scene.addItem(count_text)
            self._items.append(count_text)

            self._mini_entries.append({
                "item_id": item_id,
                "text": count_text,
                "last_count": -1,
                "stack_max": data["stack_max"]
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
        self._current_pv = pv
        self._current_pv_max = pv_max
        self._apply_heart_display(pv, pv_max)

    def _apply_heart_display(self, pv, pv_max):
        for i, (full, half, empty) in enumerate(self._heart_triples):
            heart_value = pv-i
            if heart_value >= 1:
                full.show()
                half.hide()
                empty.hide()
            elif 1 > heart_value >= 0.5:
                full.hide()
                half.show()
                empty.hide()
            else:
                full.hide()
                half.hide()
                empty.show()


    def update_hud(self, player, inventory, scene):
        
        self.update_hearts(player.pv_main, player._pv_max)
        
        # mana
        mana_count = inventory.count_item("mana")
        ratio = min(mana_count / max(self._mana_max, 1), 1.0)
        fill_w = int(self.mana_bar_w * ratio)
        self._mana_bar_fill.setRect(self.heart_margin_left, self._mana_bar_y, fill_w, self.mana_bar_h)
        
        # touches
        self._attack_key_label.setPlainText(QKeySequence(settings.keys["ATTACK"]).toString())
        self._item_key_label.setPlainText(QKeySequence(settings.keys["ITEM"]).toString())
        
        #update d'epee
        sword_path = "assets/items/sword.png"
        
        if scene.get_flag("sword_upgrade"):
                sword_path = "assets/items/sword_upgrade.png"
        elif scene.get_flag("sword_tungsten"):
                sword_path = "assets/items/sword_tungsten"

        # mise a jour si palier a change
        if getattr(self, "_cache_sword_path", None) != sword_path:
            self._cache_sword_path = sword_path
            pix = QPixmap(sword_path)
            if not pix.isNull():
                icon_size = int(self._box_size - self.box_padding)
                self._weapon_icon.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.FastTransformation))
                
        # item equipe a change
        if getattr(self, "_cache_sword_path", None) != sword_path:
            self._cache_sword_path = sword_path 
            pix = QPixmap(sword_path)
            if not pix.isNull():
                icon_size = int(self._box_size - self.box_padding)
                self._weapon_icon.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.FastTransformation))

        # update de l'item equipe
        if self._item_icon is not None:
            equipped_id = inventory._equipped_item_id
            count = inventory.count_item(equipped_id) if equipped_id else 0
            has_item = count > 0

            current_equip_state = (equipped_id, has_item)
            
            if getattr(self, "_cache_equip_state", None) != current_equip_state:
                self._cache_equip_state = current_equip_state 
                
                if equipped_id and has_item:
                    from game.item_registry import get_item_data
                    data = get_item_data(equipped_id)
                    if data:
                        pix = QPixmap(data["icon_path"])
                        if not pix.isNull():
                            icon_size = int(self._box_size - self.box_padding)
                            self._item_icon.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.FastTransformation))
                        else:
                            self._item_icon.setPixmap(QPixmap())
                    else:
                        self._item_icon.setPixmap(QPixmap())
                else:
                    self._item_icon.setPixmap(QPixmap())

        # update mini inventaire
        for entry in self._mini_entries:
            count = inventory.count_item(entry["item_id"])
            
            if count != entry["last_count"]:
                entry["last_count"] = count
                entry["text"].setPlainText(f"x{count}")
                
                # jaune si max atteint
                if count >= entry["stack_max"]:
                    entry["text"].setDefaultTextColor(QColor(235, 211, 32))
                else:
                    entry["text"].setDefaultTextColor(QColor(220, 220, 220))

    # ------------------------------------------------------------------
    # utilitaire
    # ------------------------------------------------------------------

    def get_items(self):
        """
        Retourne tous les QGraphicsItems du HUD.
        A passer a persistent_items de GameScene pour qu'ils survivent aux changements de salle.
        """
        return list(self._items)
