# -*- coding: utf-8 -*-

import json
import os
from PyQt5.QtCore import Qt
from game.config import BASE_TILE_SIZE, BASE_SPEED_pxl

KEYS_AZERTY = {
    "UP": Qt.Key_Up, "LEFT": Qt.Key_Left, "RIGHT": Qt.Key_Right, "DOWN": Qt.Key_Down,
    "SPRINT": Qt.Key_Shift, "CROUCH": Qt.Key_Control, 
    "PAUSE": Qt.Key_Tab,
    "LEAVE": Qt.Key_Escape, 
    "INTERACT": Qt.Key_Q, 
    "ATTACK": Qt.Key_W,
    "ITEM": Qt.Key_X, 
    "INVENTORY": Qt.Key_C, 
    "SHOUTS": Qt.Key_M, 
    "CONFIRM": Qt.Key_Return
}

KEYS_QWERTY = {
    "UP": Qt.Key_Up, "LEFT": Qt.Key_Left, "RIGHT": Qt.Key_Right, "DOWN": Qt.Key_Down,
    "SPRINT": Qt.Key_Shift, "CROUCH": Qt.Key_Control, 
    "PAUSE": Qt.Key_Tab,
    "LEAVE": Qt.Key_Escape, 
    "INTERACT": Qt.Key_A, 
    "ATTACK": Qt.Key_Z,
    "ITEM": Qt.Key_X, 
    "INVENTORY": Qt.Key_C, 
    "SHOUTS": Qt.Key_M, 
    "CONFIRM": Qt.Key_Return
}

class Settings:
    def __init__(self, filepath="settings.json"):
        self.filepath = filepath
        
        # --- Valeurs par défaut ---
        self.scale = 3.0
        self.resolution_index = 0
        self.control_scheme = "azerty"
        self.music_volume = 1
        self.sfx_volume = 0.75
        self.crt_overlay = True
        
        self.load()

    @property
    def keys(self):
        return KEYS_QWERTY if self.control_scheme == "qwerty" else KEYS_AZERTY

    @property
    def tile_size(self):
        return BASE_TILE_SIZE * self.scale

    @property
    def base_speed(self):
        return BASE_SPEED_pxl * self.scale
        

    def load(self):
        """Charge les parametres depuis le fichier JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.scale = data.get("scale", self.scale)
                    self.resolution_index = data.get("resolution_index", self.resolution_index)
                    self.control_scheme = data.get("control_scheme", self.control_scheme)
                    self.music_volume = data.get("music_volume", self.music_volume)
                    self.sfx_volume = data.get("sfx_volume", self.sfx_volume)
                    self.crt_overlay = data.get("crt_overlay", self.crt_overlay)
            except Exception as e:
                print(f"Erreur lors du chargement des paramètres : {e}")

    def save(self):
        """Sauvegarde les parametres actuels dans le fichier JSON."""
        data = {
            "scale": self.scale,
            "resolution_index": self.resolution_index,
            "control_scheme": self.control_scheme,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "crt_overlay": self.crt_overlay
        }
        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres : {e}")
            
            
#  creation d'instance globale unique
settings = Settings()