# -*- coding: utf-8 -*-
"""
Systeme d'inventaire : Item et Inventory.

item :  instance d'un objet dans un slot (item_id + quantite).
        Les proprietes (nom, icone, categorie...) sont lues depuis le catalogue.
inventory : grille de 24 slots + 2 pointeurs d'equipement (arme W, consommable X).
"""
from PyQt5.QtGui import QPixmap
from game.item_registry import get_item_data

class Item:

    # un item est défini par son id et sa quantité (le reste des infos vient du registre)
    def __init__(self, item_id, count = 1):
        self.item_id = item_id
        self.count = count
        self._icon_cache = None

    @property
    def data(self):
        return get_item_data(self.item_id)

    @property
    def name(self):
        return self.data["name"] 

    @property
    def icon_path(self):
        return self.data["icon_path"] 
    
    @property
    def category(self):
        return self.data["category"] 
    @property
    def stack_max(self):
        return self.data["stack_max"]

    @property
    def effect(self):
        return self.data["effect"]
    @property
    def icon(self):
        if self._icon_cache is None: 
            self._icon_cache = {}
            self._icon_cache[self.icon_path] = QPixmap(self.icon_path) # lazy loading pour gagner en perf
        return self._icon_cache[self.icon_path]



class Inventory():

# inventory est une grille de 24 slots + 2 pointeurs d'equipement (arme W, consommable X).
    def __init__(self, total_slots=24):
        self.total_slots = total_slots
        self._slots = [None]*total_slots
        self._dirty = True

        self._equipped_weapon_id = "sword"
        self._equipped_consumable_id = None

# acces au slots 

    def set_slot(self, index, item):
        if not (0 <= index < self.total_slots):
            return
        self._slots[index] = item
        self._dirty = True

    def get_slot(self, index):
        if 0 <= index < self.total_slots:
            return self._slots[index]
        return None
        
# dirty flag
    def is_dirty(self):
        return self._dirty

    def clear_dirty(self):
        self._dirty = False

# ajout / recherche / consommation

    def add_item(self, item_id, count=1):
        """
        Ajoute un item a l'inventaire (stack existant ou nouveau slot).
        Retourne True si l'ajout a reussi, False si inventaire plein.
        """
        data = get_item_data(item_id)
        if data is None:
            return False
        stack_max = data["stack_max"]

        remaining = count

        # 1) chercher un stack existant non plein
        for i in range(self.total_slots):
            if remaining <= 0:
                break
            slot = self._slots[i]
            if slot is not None and slot.item_id == item_id and slot.count < stack_max:
                space = stack_max - slot.count
                added = min(remaining, space)
                slot.count += added
                remaining -= added
                self._dirty = True

        # 2) creer de nouveaux stacks dans les slots vides
        for i in range(self.total_slots):
            if remaining <= 0:
                break
            if self._slots[i] is None:
                added = min(remaining, stack_max)
                self._slots[i] = Item(item_id, added)
                remaining -= added
                self._dirty = True

        return remaining <= 0


    def has_item(self, item_id):
        for slot in self._slots:
            if slot is not None and slot.item_id == item_id:
                return True
        return False 

    def count_item(self, item_id):
        total = 0
        for slot in self._slots:
            if slot is not None and slot.item_id == item_id:
                total += slot.count
        return total


    def consume_one(self, item_id):
        for i in range(self.total_slots):
            slot = self._slots[i]
            if slot is not None and slot.item_id == item_id:
                slot.count  -= 1
                if slot.count  == 0:
                    self.set_slot(i, None)
                self._dirty = True
                return True
        return False
 # equipement       
    def equip_weapon(self, item_id):
        self._equipped_weapon_id = item_id
        self._dirty = True

    def equip_consumable(self, item_id):
        self._equipped_consumable_id = item_id
        self._dirty = True

    @property
    def equiped_weapon_id(self):
        return self._equipped_weapon_id

    @property 
    def equiped_consumable_id(self):
        return self._equipped_consumable_id

# reset inventory
    def reset(self):
        """Vide tous les slots (nouveau jeu ou mort)."""
        self._slots = [None] * self.total_slots
        self._dirty = True
        self._equipped_weapon_id = "sword"
        self._equipped_consumable_id = None

# gestion save

    def to_save_data(self):
        """Convertit l'inventaire en dictionnaire serialisable (JSON)."""
        slots_data = []
        for i, slot in enumerate(self._slots):
            if slot is not None:
                slots_data.append({
                    "slot":    i,
                    "item_id": slot.item_id,
                    "count":   slot.count,
                })
        return {
            "slots":              slots_data,
            "equipped_weapon":    self._equipped_weapon_id,
            "equipped_consumable": self._equipped_consumable_id,
        }

    def from_save_data(self, data):
        if not data:
            return
        self._slots = [None] * self.total_slots
        for entry in data.get("slots", []):
            index   = entry["slot"]
            item_id = entry["item_id"]
            count   = entry["count"]
            if 0 <= index < self.total_slots:
                self._slots[index] = Item(item_id, count)
        self._equipped_weapon_id     = data.get("equipped_weapon", "sword")
        self._equipped_consumable_id = data.get("equipped_consumable")
        self._dirty = True