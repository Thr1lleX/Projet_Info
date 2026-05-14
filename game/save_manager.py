# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

import json
import os
import shutil


class SaveManager:
    SAVE_DIR = "savefiles"
    
    def __init__(self, slot=None):
        self.slot = slot
        self.template_path = f"{self.SAVE_DIR}/file0.json"
        
        if slot is not None:
            self.save_path = f"{self.SAVE_DIR}/file{slot}.json"
        else:
            self.save_path = None

        self.data = {}

        self.load()

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------

    def load(self):
        # si la sauvegarde n'existe pas, on charge file0
        if self.save_path is None:
        
            with open(self.template_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        
            return
        
        if not os.path.exists(self.save_path):
            return

        with open(self.save_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    @classmethod
    def write_save(cls, slot, data):
        """
        Ecrit une sauvegarde dans un slot.
        """
    
        os.makedirs(cls.SAVE_DIR, exist_ok=True)
    
        path = os.path.join(
            cls.SAVE_DIR,
            f"file{slot}.json"
        )
    
        with open(path, "w", encoding="utf-8") as file:
    
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )
    def save(self):
        """
        sauvegarde les donnees dans le slot defini, utilise pr load derniere save
        """
        if self.slot is not None:
            SaveManager.write_save(self.slot, self.data)

    # ---------------------------------------------------------
    # FLAGS
    # ---------------------------------------------------------

    def get_flag(self, name):
        return self.data.get("flags", {}).get(name, False)

    def set_flag(self, name, value=True):
        self.data.setdefault("flags", {})
        self.data["flags"][name] = value

        self.save()
        
    # ---------------------------------------------------------
    # HEALTH
    # ---------------------------------------------------------
    
    def get_current_health(self):
        return self.data.get("current_health", 6)
    
    def set_current_health(self, value):
    
        self.data["current_health"] = value
    
        self.save()

    # ---------------------------------------------------------
    # PLAYER / ROOM
    # ---------------------------------------------------------

    def get_current_room(self):
        return self.data.get("current_room", "room3")

    def set_current_room(self, room_name):
        self.data["current_room"] = room_name
        self.save()

    def get_player_position(self):
        return (
            self.data.get("player_x", 5),
            self.data.get("player_y", 5)
        )

    def set_player_position(self, x, y):
        self.data["player_x"] = x
        self.data["player_y"] = y

        self.save()


    @staticmethod
    def save_exists(slot):
        return os.path.exists(f"savefiles/file{slot}.json")
    @staticmethod
    def any_save_exists():
    
        return (
            SaveManager.save_exists(1)
            or SaveManager.save_exists(2)
            or SaveManager.save_exists(3)
        )
