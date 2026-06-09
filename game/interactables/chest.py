# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from game.interactables.interactable import Interactable
from game.config import DEBUG
from game.item_registry import ITEM_CATALOG

from game.settings import settings

class Chest(Interactable):
    """Coffre interactif contenant du butin (loot) recupere par le joueur."""
    def __init__(self, scale, x, y, loot_data, room_name):
        super().__init__(scale)
        self.type = "chest"
        self.collision = 1 
  
        # gestion du loot flexible
        if not loot_data:
            self.loot_id = None
            self.amount = 0
        if isinstance(loot_data, list):
            self.loot_id = loot_data[0] if len(loot_data) > 0 else None
            self.amount = loot_data[1] if len(loot_data) > 1 else 1
        else:
            self.loot_id = loot_data
            self.amount = 1
        
        self.room_name = room_name
        
        # position du la grille pour generer flag unique
        self.grid_x = int(x // settings.tile_size)
        self.grid_y = int(y // settings.tile_size) 
        
        self.flag_name = f"opened_chest_{self.room_name}_{self.grid_x}_{self.grid_y}"
        
        self.is_open = False

        self.img_closed = QPixmap("assets/chest_closed.png")
        self.img_open = QPixmap("assets/chest_open.png")
        
        self.img_closed = self.img_closed.scaled(int(settings.tile_size), int(settings.tile_size))
        self.img_open = self.img_open.scaled(int(settings.tile_size), int(settings.tile_size))

        self.x = x
        self.y = y
        self.update_graphics()

    def update_graphics(self):
        """Surcharge pour choisir la bonne image selon l'etat du coffre."""
        super().update_graphics()
        
        if self.is_open:
            self.setPixmap(self.img_open)
        else:
            self.setPixmap(self.img_closed)    
    

    def interact(self, scene, player=None):
        """Ouvre le coffre, recupere le butin et affiche un message au joueur."""
        # check si ouvert
        if scene.current_save.get_flag(self.flag_name) or scene.session_flags.get(self.flag_name):
            return 

        # ouvre coffre sinon
        scene.sfx_manager.play("snd_chest")
        self.is_open = True
        self.update_graphics()
        
        # marque flag d'ouverture
        scene.session_flags[self.flag_name] = True # On marque le coffre comme ouvert
        if DEBUG:
            print(f"[CHEST] : Coffre ouvert déclenche flag {self.flag_name}")
        
        # calcul du nom pour l'affichage (pluriel mdr & gestion d'erreur)
        if not self.loot_id or self.loot_id == "none":
            item_display_name = "RIEN"
            if DEBUG: print(f"[DEBUG] Coffre à {self.grid_x},{self.grid_y} est vide.")
        else:
            item_display_name = ITEM_CATALOG[self.loot_id]["name"].capitalize()
            if self.amount > 1:
                suffix = "" if self.loot_id.endswith('s') else "s"
                item_display_name = f"{self.amount} {item_display_name}{suffix}"
            scene.screen_manager.inventory.add_item(self.loot_id, self.amount)

        if self.loot_id in ITEM_CATALOG:
            item_info = ITEM_CATALOG[self.loot_id]
            if item_info.get("category") == "permanent":
                name_flag = item_info.get("required_flag")
                if name_flag:
                    scene.session_flags[name_flag] = True
                    scene.screen_manager.inventory.add_item(name_flag, 1)

        if hasattr(scene, "dialogue_manager") and scene.dialogue_manager:
            scene.dialogue_manager.start_text(f"Vous obtenez : {item_display_name}!", font="font2")
            if hasattr(scene, "player"):
                scene.player.obtain_item(self.loot_id)