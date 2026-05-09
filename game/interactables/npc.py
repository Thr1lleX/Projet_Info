# -*- coding: utf-8 -*-

from game.interactables.interactable import Interactable
from game.animspr import load_animation_sequence
from game.config import SCALE, DEBUG

class NPC(Interactable):
    def __init__(self, scale, x, y, npc_type=None, dialogue_id=None):
        super().__init__(scale) 

        self.type = "npc"
        self.npc_type = npc_type
        self.dialogue = dialogue_id

        self.x = x
        self.y = y

        # animation
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_duration = 0.5 #2 fois plus longtemps que tiles

        if self.npc_type:
            sprite_path = f"assets/npc/{self.npc_type}"
            # On charge la sequence (identique au SavePoint)
            self.frames = load_animation_sequence(sprite_path, size=(1, 1))

            if self.frames:
                self.setPixmap(self.frames[0])
        
        self.update_graphics()

    def update(self, dt):
        """
        Gère le défilement des images de l'animation.
        Cette méthode est appelée à chaque frame par la GameScene.
        """
        if not self.frames or len(self.frames) <= 1:
            return

        self.animation_timer += dt

        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            self.setPixmap(self.frames[self.current_frame])

    def interact(self, scene, player=None):
        if self.dialogue:
            if DEBUG: print(f"Interaction avec {self.npc_type}, dialogue : {self.dialogue}")
            if hasattr(scene, "dialogue_manager") and scene.dialogue_manager:
                scene.dialogue_manager.start(self.dialogue)