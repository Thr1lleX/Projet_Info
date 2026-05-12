# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from game.interactables.interactable import Interactable
from game.config import SCALE, TILE_SIZE, DEBUG
from game.item_registry import ITEM_CATALOG

class Chest(Interactable):
    def __init__(self, scale, x, y, loot_data, room_name):
        super().__init__(scale)
        self.type = "chest"
        self.collision = 1 
  
        # gestion du loot flexible
        if isinstance(loot_data, list):
            self.loot_id = loot_data[0]
            self.amount = loot_data[1]
        else:
            self.loot_id = loot_data
            self.amount = 1
        
        self.room_name = room_name
        
        # position du la grille pour generer flag unique
        self.grid_x = int(x // TILE_SIZE)
        self.grid_y = int(y // TILE_SIZE) 
        
        self.flag_name = f"opened_chest_{self.room_name}_{self.grid_x}_{self.grid_y}"
        
        self.is_open = False

        self.img_closed = QPixmap("assets/chest_closed.png")
        self.img_open = QPixmap("assets/chest_open.png")
        
        self.img_closed = self.img_closed.scaled(int(self.tile_size), int(self.tile_size))
        self.img_open = self.img_open.scaled(int(self.tile_size), int(self.tile_size))

        self.x = x
        self.y = y
        self.update_graphics()

    def update_graphics(self):
        """
        surcharge pour choisir la bonne image selon le flag
        """
        super().update_graphics()
        
        if self.is_open:
            self.setPixmap(self.img_open)
        else:
            self.setPixmap(self.img_closed)

    def interact(self, scene, player=None):
        # check si ouvert
        if scene.current_save.get_flag(self.flag_name):
            return 

        # ouvre coffre sinon
        scene.sfx_manager.play("snd_chest")
        self.is_open = True
        self.update_graphics()
        
        # marque flag d'ouverture
        scene.current_save.set_flag(self.flag_name, True)
        
        # calcul du nom pour l'affichage (pluriel mdr)
        item_display_name = self.loot_id.capitalize()
        if self.amount > 1:
            if not self.loot_id.endswith('s'):
                item_display_name = f"{self.amount} {item_display_name}s"
            else:
                item_display_name = f"{self.amount} {item_display_name}"
        else:
            item_display_name = f"{item_display_name}"


        success = scene.screen_manager.inventory.add_item(self.loot_id, self.amount)
        
        if success:
            if DEBUG:
                print(f"Coffre ouvert : obtenu {self.loot_id}")
            if ITEM_CATALOG[self.loot_id]["category"] == "permanent":
                name_flag = ITEM_CATALOG[self.loot_id]["required_flag"]
                scene.current_save.set_flag(name_flag, True)
                scene.screen_manager.inventory.add_item(name_flag, 1)
            if hasattr(scene, "dialogue_manager") and scene.dialogue_manager:
                  scene.dialogue_manager.start_text(f"Vous obtenez : {item_display_name}!",font="font2")