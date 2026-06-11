# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

from game.interactables.interactable import Interactable
from game.animspr import load_animation_sequence
from game.config import DEBUG, GRID_HEIGHT,HUD_HEIGHT,GRID_WIDTH
import random 
from game.settings import settings

class NPC(Interactable):
    """Personnage non-joueur interactif avec dialogues conditionnels et animations."""
    def __init__(self, 
                 scale, 
                 x, 
                 y, 
                 npc_type=None, 
                 dialogue_id=None,
                 conditional_rules=None,
                 spawn_if=None,
                 despawn_if=None,
                 spawn_transition=None,
                 despawn_transition=None,
                 scene = None,
                 size = None
        ):
        super().__init__(scale)


        self.type = "npc"
        self.npc_type = npc_type

        self.x = x
        self.y = y
        self.size = size or (1, 1)
        self.hitbox_width = self.size[0] * settings.tile_size
        self.hitbox_height = self.size[1] * settings.tile_size              
        
        self.target_x = x
        self.target_y = y
        
        self.scene = scene
        
        self.room_name = self.scene.current_room
                
        
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
        
        # spawn/despawn
        self.spawn_if = spawn_if
        self.despawn_if = despawn_if
        
        self.spawn_transition = spawn_transition or {}
        self.despawn_transition = despawn_transition or {}
        
        self.is_despawning = False
        
        self.slide_speed = 0
        self.slide_direction = None
        
        # nametag
        tile_x = int(self.target_x / settings.tile_size)

        tile_y = int(
            (self.target_y / settings.tile_size) - HUD_HEIGHT
        )
                
        self.spawn_memory_flag = (
            f"has_spawned_"
            f"{self.npc_type}_"
            f"{self.room_name}_"
            f"{tile_x}_"
            f"{tile_y}"
        )
                
        # animation
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_duration = 0.5 #2 fois plus longtemps que tiles
        
        # spawn_transition fondu
        self.opacity = 1.0
        self.fade_speed = 0
        self.fade_direction = None  # "in" ou "out"
        
        self.setOpacity(self.opacity)

        if self.npc_type:
            sprite_path = f"assets/npc/{self.npc_type}"
            # on charge la sequence (identique au SavePoint)
            self.frames = load_animation_sequence(sprite_path, size=self.size)

            if self.frames:
                self.setPixmap(self.frames[0])
        self.was_auto_interact = False      
        
        self.update_graphics()
        self.init_transition()
    
    def init_transition(self):
        """Initialise le deplacement d'apparition du NPC depuis l'exterieur de l'ecran."""
        if self.scene.get_flag(self.spawn_memory_flag):
            return
    
        
        transition_type = self.spawn_transition.get("type")
        
        if transition_type == "slide":        
            direction = self.spawn_transition.get("direction", "down")
        
            screen_w = GRID_WIDTH * settings.tile_size
            screen_h = (GRID_HEIGHT + HUD_HEIGHT) * settings.tile_size
        
            margin = settings.tile_size * 2
        
            # spawn hors écran
            if direction == "down":
                self.y = screen_h + margin
        
            elif direction == "up":
                self.y = -margin
        
            elif direction == "left":
                self.x = -margin
        
            elif direction == "right":
                self.x = screen_w + margin
        
            self.start_slide(direction,self.spawn_transition.get("speed", 1.0))
            self.scene.current_save.data["flags"][self.spawn_memory_flag] = True
            
        elif transition_type == "fade":
            self.opacity = 0.0
            self.setOpacity(self.opacity)
            self.start_fade("in", self.spawn_transition.get("speed", 0.03))
            self.scene.current_save.data["flags"][self.spawn_memory_flag] = True
        
    def update(self, dt,scene=None):
        """Gere le defilement de l'animation, les deplacements (slide) et les disparitions."""
        # despawn
        if (scene and self.despawn_if and scene.get_flag(self.despawn_if) and not self.is_despawning):
            self.is_despawning = True
        
            transition = self.despawn_transition
            if getattr(self, "was_auto_interact", False) and hasattr(scene, "player") and scene.player:
                scene.player.is_cinematic = False
        
            transition = self.despawn_transition                                                                                      
        
            if transition.get("type") == "slide":
                self.start_slide(
                    transition.get("direction", "down"),
                    transition.get("speed", 1.0)
                )
            elif transition.get("type") == "fade":
                self.start_fade("out", transition.get("speed", 0.03))
            else:
                scene.removeItem(self)
                scene.interactables.remove(self)
                return
        # suppression apres sortie ecran
        if self.is_despawning:
            if self.despawn_transition.get("type") == "fade" and self.opacity <= 0.0:
                scene.removeItem(self)
                if self in scene.interactables:
                    scene.interactables.remove(self)
                return
            elif self.despawn_transition.get("type") == "slide":
                limit = (GRID_HEIGHT+ HUD_HEIGHT + 2) * settings.tile_size
            
                if self.y > limit:
                    scene.removeItem(self)
            
                    if self in scene.interactables:
                        scene.interactables.remove(self)
            
                    return
        # fade
        if self.fade_direction:
            fade_amount = self.fade_speed * dt * 60
            if self.fade_direction == "in":
                self.opacity += fade_amount
                if self.opacity >= 1.0:
                    self.opacity = 1.0
                    self.fade_direction = None # transition terminee
            elif self.fade_direction == "out":
                self.opacity -= fade_amount
                if self.opacity <= 0.0:
                    self.opacity = 0.0
            self.setOpacity(self.opacity)
        
        # slide
        if self.slide_direction:
            speed = self.slide_speed * dt * 60
            # on inverse la direction si on sort, et on ne check pas le target
            if self.is_despawning:
                if self.slide_direction == "down":
                    self.y -= speed
                elif self.slide_direction == "up":
                    self.y += speed
                elif self.slide_direction == "left":
                    self.x += speed
                elif self.slide_direction == "right":
                    self.x -= speed
            else:
                if self.slide_direction == "down":
                    self.y += speed
                    if self.y >= self.target_y:
                        self.y = self.target_y
                        self.slide_direction = None
                elif self.slide_direction == "up":
                    self.y -= speed
                    if self.y <= self.target_y:
                        self.y = self.target_y
                        self.slide_direction = None
                elif self.slide_direction == "left":
                    self.x -= speed
                    if self.x <= self.target_x:
                        self.x = self.target_x
                        self.slide_direction = None
                elif self.slide_direction == "right":
                    self.x += speed
                    if self.x >= self.target_x:
                        self.x = self.target_x
                        self.slide_direction = None
                        self.slide_direction = None
                        
        if not self.slide_direction and not self.is_despawning and not self.fade_direction:
            if getattr(self, "auto_interact", False):
                self.was_auto_interact = True
                self.interact(scene)
                self.auto_interact = False                        
        
        self.update_graphics()
        
        # NPC NON STATIQUE
        if not self.frames or len(self.frames) <= 1:
            return
        
        # animation
        self.animation_timer += dt

        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            self.setPixmap(self.frames[self.current_frame])
            
    def check_conditions(self, scene):
        """Verifie les conditions de flags pour lancer le dialogue approprie."""
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
        """Declenche le dialogue et joue un son aleatoire specifique au NPC."""
        if self.slide_direction is not None or self.is_despawning or self.fade_direction is not None:
            return #bloque interaction si slide
        self.check_conditions(scene)
        
        # gestion du son
        if self.type != "sign":
            if hasattr(scene, "sfx_manager") and scene.sfx_manager:
                base_voice_key = f"snd_{self.npc_type}"
                
                # on recupere toutes les cles qui commencent par le nom (ex: snd_old_man, snd_old_man1, snd_old_man2)
                available_sounds = [key for key in scene.sfx_manager.sounds.keys() if key.startswith(base_voice_key)]
                
                if available_sounds:
                    chosen_voice = random.choice(available_sounds)
                    scene.sfx_manager.play(chosen_voice)
                else:
                    scene.sfx_manager.play("snd_npc")
        
        # gestion de l'interaction
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

    def start_slide(self, origin_direction, speed=1.0):
        """Demarre un deplacement glisse dans une direction donnee."""
        self.slide_speed = speed * settings.scale
    
        movement_map = {
            "down": "up",
            "up": "down",
            "left": "right",
            "right": "left"
        }
    
        self.slide_direction = movement_map[origin_direction]
            
    def start_fade(self, direction="out", speed=0.03):
        """
        demarre un fondu (sortant ou entrant)
        """
        self.fade_direction = direction
        self.fade_speed = speed