# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from game.entity import Entity
from game.settings import settings
from game.config import DEBUG
import random

class CrystalSwitch(Entity):
    """Interrupteur de cristal changeant d'etat au moindre coup, modifiant la disposition de la salle."""
    def __init__(self, scale, x, y):
        super().__init__(scale)
        self.x = x
        self.y = y
        
        self.speed = 0
        self.collision = 1 
        self.is_effect_immune = True 
        self.knockback = 0

        self.img_blue = QPixmap("assets/blue_crystal.png").scaled(
            settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
        )
        self.img_red = QPixmap("assets/red_crystal.png").scaled(
            settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
        )
        
        self.current_state = None
        self.setPos(self.x, self.y)

    def update(self, dt,scene):
        
        self.sync_with_global_state()
        
        self.update_damage_state(dt)
        self.update_graphics()
        
    def update_graphics(self):
        """Synchronise l'etat avant de dessiner (appele juste apres le spawn)."""
        # on synchronise avant de dessiner
        self.sync_with_global_state()
        super().update_graphics()
        
    def sync_with_global_state(self):
        """Verifie le flag global et met a jour l'interrupteur si necessaire."""
        scene = self.scene()
        if scene and hasattr(scene, "get_flag"):
            is_blue = scene.get_flag("blue_switch")
            
            if is_blue != self.current_state:
                self.current_state = is_blue
                self.update_appearance(is_blue)

    def update_appearance(self, is_blue):
        pix = self.img_blue if is_blue else self.img_red
        
        self.sprites = {
            "up": pix,
            "down": pix,
            "left": pix,
            "right": pix
        }

    def take_damage(self, scene, damage, source=None):
        """Change l'etat de l'interrupteur au moindre coup (inverse le flag global)."""
        if self.is_invulnerable:
            return
            
        # inversion du flag
        new_state = not scene.get_flag("blue_switch")
        scene.session_flags["blue_switch"] = new_state
        
        if DEBUG: print(f"[FLAG] : Set flag 'blue_switch' {new_state}")
        
        # mise a jour des blocs de la salle
        if hasattr(scene, "toggle_crystal_blocks"):
            scene.toggle_crystal_blocks()
            
        scene.sfx_manager.play("snd_switch")
        
        # effets degats
        self.is_damaged = True
        self.damage_timer = 0
        self.is_invulnerable = True
        self.invuln_timer = 0
        self.invuln_duration = 0.2 # meme que player.attack_delay = 0.2
        #self.apply_white_flash() # enelve car cree pb de clignotement de spr

    def die(self): pass # indestructible

    def interact(self, scene, player=None):
        """Affiche un texte amusant lorsqu'on interagit avec Michel le cristal."""
        if random.random() < 0.66:
            voice = "snd_michel1"
        else: 
            voice = "snd_michel2"
        scene.sfx_manager.play(voice)
        
        if "blue_switch" not in scene.session_flags:
            dialogues = [
                "Salut, moi c'est Michel.",
                "J'adore quand on me frappe. Tu devrais faire ça."
            ]
        else:
            is_blue = scene.session_flags["blue_switch"]
            if is_blue:
                dialogues = [
                    "Je suis bleu maintenant!",
                    "La couleur de la mer m'emplit de calmitude."
                    ]
            else:
                dialogues = [
                    "Ah! je suis de nouveau rouge.",
                    "J'aime bien, c'est la couleur du sang de mes ennemis après que je les avoir mis en pièces."
                ]

        if hasattr(scene, "dialogue_manager"):
            scene.dialogue_manager.start_text(dialogues,"font4")