# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
"""
Systeme d'inventaire : Item et Inventory.

item :  instance d'un objet dans un slot (item_id + quantite).
        Les proprietes (nom, icone, categorie...) sont lues depuis le catalogue.
inventory : grille de 24 slots + 2 pointeurs d'equipement (arme W, consommable X).
"""
from PyQt5.QtGui import QPixmap
from game.item_registry import get_item_data
from game.config import DEBUG

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
            
    @property
    def slot(self):
        return self.data.get("slot")



class Inventory():

# inventory est une grille de 24 slots + 2 pointeurs d'equipement (arme W, consommable X).
    def __init__(self, total_slots=24):
        self.total_slots = total_slots
        self._slots = [None]*total_slots
        self._dirty = True
        self._collectibles = {} #pr stocker cles, gold etc. qui ne sont pas utilisables

        self._equipped_item_id = None

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
        Ajoute un item a l'inventaire dans son slot predefini.
        Retourne True si l'ajout a reussi, False si inventaire plein.
        """
        data = get_item_data(item_id)
        if data is None:
            return False
            
        stack_max = data["stack_max"]
        target_slot = data.get("slot")
        
        # cas 1: l'item est collectible
        if target_slot is None:
            if item_id not in self._collectibles:
                self._collectibles[item_id] = 0
                
            stack_max = data.get("stack_max", 999)
            new_count = self._collectibles[item_id] + count
            self._collectibles[item_id] = min(new_count, stack_max)
            
            self._dirty = True
            return True

        # # verifier que l'item est bien dans un solt
        # if target_slot is None or not (0 <= target_slot < self.total_slots):
        #     if DEBUG:
        #         print(f"Erreur : L'item {item_id} n'a pas de slot valide assigné.")
        #     return False

        current_item_in_slot = self._slots[target_slot]

        # si slot vide on place objet
        if current_item_in_slot is None:
            added = min(count, stack_max)
            self._slots[target_slot] = Item(item_id, added)
            self._dirty = True
            return True

        # si slot continent deja objet on place la quantite
        elif current_item_in_slot.item_id == item_id:
            space_left = stack_max - current_item_in_slot.count
            if space_left > 0:
                added = min(count, space_left)
                current_item_in_slot.count += added
                self._dirty = True
                return True
            else:
                return False

        #si le slot est deja occupe par un autre objet (normalement pas de pb)
        else:
            if DEBUG:
                print(f"Erreur : Conflit de slot. {item_id} tente d'écraser {current_item_in_slot.item_id}.")
            return False


    def has_item(self, item_id):
        for slot in self._slots:
            if slot is not None and slot.item_id == item_id:
                return True
        return False 

    def count_item(self, item_id):
        # compte collectibles d'abord
        if item_id in self._collectibles:
            return self._collectibles[item_id]
        
        # sinon cherche dans la grille
        total = 0
        for slot in self._slots:
            if slot is not None and slot.item_id == item_id:
                total += slot.count
        return total


    def consume_one(self, item_id):
        # si c'est un collectible
        if item_id in self._collectibles:
            if self._collectibles[item_id] > 0:
                self._collectibles[item_id] -= 1
                self._dirty = True
                return True
            return False
        
        #sinon, est dans slot
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
    def equip_item(self, item_id):
        self._equipped_item_id = item_id
        self._dirty = True

    @property
    def equiped_item_id(self):
        return self._equipped_item_id

# reset inventory
    def reset(self):
        """Vide tous les slots (nouveau jeu ou mort)."""
        self._slots = [None] * self.total_slots
        self._dirty = True
        self._equipped_item_id = None

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
            "collectibles": self._collectibles,
            "equipped_item": self._equipped_item_id,
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
        self._collectibles = data.get("collectibles", {})
        self._equipped_item_id = data.get("equipped_item")
        self._dirty = True

# gestion des items permanents, on les a si flag verifie


    def sync_permanent_items(self, flags_dict):
        # import local pour éviter les imports circulaires
        from game.item_registry import ITEM_CATALOG 
        
        for item_id, data in ITEM_CATALOG.items():
            required_flag = data.get("required_flag")
            
            if required_flag and flags_dict.get(required_flag) is True:
                self.add_item(item_id, 1)
