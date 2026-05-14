# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

from game.interactables.interactable import Interactable
from game.animspr import load_animation_sequence
from game.config import SCALE, DEBUG

class NPC(Interactable):
    def __init__(self, scale, x, y, npc_type=None, dialogue_id=None,conditional_rules=None):
        super().__init__(scale) 

        self.type = "npc"
        self.npc_type = npc_type

        self.x = x
        self.y = y
        
        
        # recuperation du dialogue, on normalise pr que ce soit une liste
        if isinstance(dialogue_id, str):
            self.base_dialogue = [dialogue_id]
        elif isinstance(dialogue_id, list):
            self.base_dialogue = dialogue_id
        else:
            self.base_dialogue = []
        
        # on stocke les regles conditionnelles pr pouvoir recharger dans meme salle
        self.conditional_rules = conditional_rules or []
        self.active_dialogue_list = list(self.base_dialogue)
        
        self.current_dialogue_index = 0 
        
        # animation
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_duration = 0.5 #2 fois plus longtemps que tiles

        if self.npc_type:
            sprite_path = f"assets/npc/{self.npc_type}"
            # on charge la sequence (identique au SavePoint)
            self.frames = load_animation_sequence(sprite_path, size=(1, 1))

            if self.frames:
                self.setPixmap(self.frames[0])
        
        self.update_graphics()

    def update(self, dt):
        """
        gere le defilement des images de l'animation.
        cette methode est appelze à chaque frame par la GameScene.
        """
        if not self.frames or len(self.frames) <= 1:
            return

        self.animation_timer += dt

        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            self.setPixmap(self.frames[self.current_frame])
            
    def check_conditions(self, scene):
        """
        fonction qui verifie si les conditions de flags sont verifiees 
        afin de lancer dialogue correspondant
        """
        dialogue = self.base_dialogue
        #new_list = list(self.base_dialogue) # Par défaut, on revient à la base

        # on parcourt les regles, la derniere l'emporte
        for rule in self.conditional_rules:
            flag = rule.get("flag")
            # if scene.current_save.get_flag(flag):
            if scene.get_flag(flag):
                dialogue = rule.get("dialogue")
                
        if isinstance(dialogue, str):
            new_list = [dialogue]
        else:
            new_list = dialogue

        # si la liste a change depuis le dernier check
        if new_list != self.active_dialogue_list:
            self.active_dialogue_list = new_list
            self.current_dialogue_index = 0 # reinitialise index 
            if DEBUG: print(f"[NPC] Changement de dialogue détecté pour {self.npc_type}")

    def interact(self, scene, player=None):
        self.check_conditions(scene)
        
        current_id = None
        if self.active_dialogue_list:
            current_id = self.active_dialogue_list[self.current_dialogue_index]
        
        if not current_id or (isinstance(current_id, str) and not current_id.strip()):
            if DEBUG: print(f"[ERREUR]: Aucun dialogue trouvé pour {self.npc_type}")
            if hasattr(scene, "dialogue_manager") and scene.dialogue_manager:
                scene.dialogue_manager.start_text("Je suis Erreur.")
            return
        
        if DEBUG: print(f"[INTERACTION] : avec {self.npc_type}, dialogue : {current_id}")
        if hasattr(scene, "dialogue_manager") and scene.dialogue_manager:
            scene.dialogue_manager.start(current_id)
            #on incremente l'index pr prochaine interaction, on bloque sur dernier element
            if self.current_dialogue_index < len(self.active_dialogue_list) - 1:
                self.current_dialogue_index += 1
