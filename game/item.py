# -*- coding: utf-8 -*-
"""
Systeme d'inventaire : Item et Inventory.

Item      : donnee d'un objet (icone, nom, quantite).
Inventory : grille de slots avec flag dirty pour synchronisation HUD.
            Les 6 premiers slots correspondent aux emplacements HUD actifs.

Pour ajouter un nouveau type d'objet :
  1. Creer une instance d'Item avec un item_id unique, une icone QPixmap, etc.
  2. L'inserer dans l'Inventory via set_slot(index, item).
"""


class Item:
    """Donnee d'un item (future-proof : icone, nom, quantite de pile)."""

    def __init__(self, item_id, icon=None, name="", stack_count=1):
        self.item_id     = item_id      # identifiant unique (str ou int)
        self.icon        = icon         # QPixmap ou None
        self.name        = name
        self.stack_count = stack_count


class Inventory:
    """
    Grille de slots.
    Les slots 0-5 correspondent aux emplacements HUD (premiere rangee active).
    Toute modification des slots HUD leve le flag dirty pour forcer la mise
    a jour du HUD au prochain tour de boucle.
    """

    def __init__(self, total_slots=30):
        self.total_slots = total_slots
        self._slots      = [None] * total_slots
        self._dirty      = False

    def set_slot(self, index, item):
        """Place ou retire un Item dans un slot (item=None pour vider)."""
        if not (0 <= index < self.total_slots):
            return
        self._slots[index] = item
        if index < 6:
            self._dirty = True

    def get_slot(self, index):
        """Retourne l'Item du slot ou None si vide / hors limites."""
        if 0 <= index < self.total_slots:
            return self._slots[index]
        return None

    def is_dirty(self):
        """True si les slots HUD ont change depuis le dernier clear_dirty."""
        return self._dirty

    def clear_dirty(self):
        self._dirty = False

    def reset(self):
        """Vide tous les slots (nouveau jeu ou mort)."""
        self._slots = [None] * self.total_slots
        self._dirty = True

    @property
    def hud_slots(self):
        """Les 6 premiers slots (actifs dans le HUD), en lecture seule."""
        return self._slots[:6]
