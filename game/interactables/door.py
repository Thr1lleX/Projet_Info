# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from game.interactables.interactable import Interactable
from game.config import DEBUG, HUD_HEIGHT

from game.settings import settings

class LockedDoor(Interactable):
    """Porte verrouillee s'ouvrant avec une cle (1 tuile)."""
    def __init__(self, scale, x, y, room_name, biome):
        super().__init__(scale)
        self.type = "locked_door"
        self.grid_x = x
        self.grid_y = y
        self.room_name = room_name
        self.biome = biome
        
        # Identifiant unique pour la sauvegarde
        self.flag_name = f"door_open_{self.room_name}_{self.grid_x}_{self.grid_y}"
        
        # Chargement des deux états
        self.pix_locked = self._load_biome_pixmap("locked_door")
        self.pix_open = self._load_biome_pixmap("door")
        
        self.is_open = False
        self.collision = 1
        
        self.x = self.grid_x * settings.tile_size
        self.y = (self.grid_y + HUD_HEIGHT) * settings.tile_size
        self.update_graphics()

    def update_graphics(self):
        """Met a jour l'affichage de la porte et desactive les collisions si ouverte."""
        if self.is_open:
            self.setPixmap(self.pix_open)
            self.collision = 0
        else:
            self.setPixmap(self.pix_locked)
            self.collision = 1
            
        super().update_graphics()

    def interact(self, scene, player=None):
        """Tente de deverrouiller la porte avec une cle de l'inventaire."""
        if self.is_open:
            return 

        inventory = scene.screen_manager.inventory
        
        if inventory.count_item("key") > 0:
            inventory.consume_one("key")
            self.is_open = True
            
            scene.session_flags[self.flag_name] = True
            
            self.update_graphics()
            scene.sfx_manager.play("snd_opendoor")
            
            if DEBUG: print("Porte deverouillee.")

        else:
            scene.sfx_manager.play("snd_locked")
            
    def _load_biome_pixmap(self, name):
        """Charge la texture specifique au biome, ou la texture par defaut."""
        path = f"assets/{self.biome}/{name}.png"
        pix = QPixmap(path)
        
        # Si non trouvé (isNull), on cherche dans default
        if pix.isNull() and self.biome != "default":
            pix = QPixmap(f"assets/default/{name}.png")
            
        return pix.scaled(settings.tile_size, settings.tile_size)