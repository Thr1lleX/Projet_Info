# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from game.interactables.interactable import Interactable
from game.config import SCALE, TILE_SIZE,DEBUG, HUD_HEIGHT

class LockedDoor(Interactable):
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
        
        self.x = self.grid_x * TILE_SIZE
        self.y = (self.grid_y + HUD_HEIGHT) * TILE_SIZE
        self.update_graphics()

    def update_graphics(self):
        if self.is_open:
            self.setPixmap(self.pix_open)
            self.collision = 0
        else:
            self.setPixmap(self.pix_locked)
            self.collision = 1
            
        super().update_graphics()

    def interact(self, scene, player=None):
        if self.is_open:
            return 

        inventory = scene.screen_manager.inventory
        
        if inventory.count_item("key") > 0:
            inventory.consume_one("key")
            self.is_open = True
            
            scene.session_flags[self.flag_name] = True
            
            self.update_graphics()
            scene.sfx_manager.play("snd_opendoor")
            
            if DEBUG: print("Porte dévérouillée.")

        else:
            scene.sfx_manager.play("snd_locked")
            
    def _load_biome_pixmap(self, name):
        path = f"assets/{self.biome}/{name}.png"
        pix = QPixmap(path)
        
        # Si non trouvé (isNull), on cherche dans default
        if pix.isNull() and self.biome != "default":
            pix = QPixmap(f"assets/default/{name}.png")
            
        return pix.scaled(TILE_SIZE, TILE_SIZE)