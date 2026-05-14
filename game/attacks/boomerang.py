# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

import math
from game.attacks.attack_entity import PersistentAttack
from game.config import TILE_SIZE
from game.dropped_item import DroppedItem

class Boomerang(PersistentAttack):
    def __init__(self, source, direction):
        speed = 8
        self.player = source
        super().__init__(
            source=self.player,
            direction=direction,
            damage=0,
            spr_path="player/attack/boomerang", 
            nb_frames=8,
            size=(1, 1),
            pos=(0, 0),
            speed=speed
        )
        
        self.only_one = True
        self.anim_speed = 7
        self.do_stun = 3
        self.can_go_on_water = True
        
        # variables de logique de boomerang
        self.start_x = self.x
        self.start_y = self.y
        self.max_travel_dist = 6
        self.returning = False
        self.base_speed = speed
        # -------------------------------------------------------

        self.raw_hitbox_data = {
            1: ((1, 13), (15, 4)),
            2: ((3, 15), (16, 2)),
            3: ((5, 14), (14, 0)),
            4: ((3, 12), (16, -1)),
            5: ((1, 10), (15, 1)),
            6: ((0, 12), (13, -1)),
            7: ((2, 14), (11, 0)),
            8: ((0, 1), (13, 15))
        }
        
        self.k = -0.75
        
        self.update_hitbox()

    def f_exp(self, x):
        """ 
        vitesse du boomerang suit loi expoentielle decroissante
        """
        return self.base_speed * (1 - math.exp(self.k * x))

    def update_position(self):
        dist_px = ((self.x - self.start_x)**2 + (self.y - self.start_y)**2)**0.5
        dist_tiles = dist_px / TILE_SIZE
        
        # etat aller
        if not self.returning:
            if dist_tiles >= self.max_travel_dist:
                self.returning = True
                self.turn_x, self.turn_y = self.x, self.y
                return
            

            # calcul de vitesse qui decroit exp plus on est proche
            # pas nulle sinon se bloque
            current_speed = max(self.f_exp(-dist_tiles + self.max_travel_dist), 0.2)
            
            move_dist = current_speed * TILE_SIZE * self.current_dt

            if self.direction == "up": self.y -= move_dist
            elif self.direction == "down": self.y += move_dist
            elif self.direction == "left": self.x -= move_dist
            elif self.direction == "right": self.x += move_dist
        
        # etat retour
        else:
            dx = self.source.x - self.x
            dy = self.source.y - self.y
            dist_to_player = (dx**2 + dy**2)**0.5

            if dist_to_player < TILE_SIZE * 0.5:
                self.die()
                return

            dist_since_turn = math.hypot(self.x - self.turn_x, self.y - self.turn_y) / TILE_SIZE
            
            current_speed = max(self.f_exp(dist_since_turn), 0.05)

            if dist_to_player > 0:
                self.x += (dx / dist_to_player) * current_speed * TILE_SIZE * self.current_dt
                self.y += (dy / dist_to_player) * current_speed * TILE_SIZE * self.current_dt

        self.setPos(self.x + self.anim_offset[0], self.y + self.anim_offset[1]) 
        
    def check_collisions(self, scene):
        """
        surcharge du systeme de collision pour gerer les items
        """
        hitbox_zone = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()

        for item in scene.items(hitbox_zone):
            if isinstance(item, DroppedItem):
                inventory = scene.screen_manager.inventory
                if inventory.add_item(item.item_id, 1):
                    if item in scene.dropped_items:
                        scene.dropped_items.remove(item)
                    scene.removeItem(item)
                    
                    if hasattr(scene, "sfx_manager"):
                        scene.sfx_manager.play("snd_item")

        super().check_collisions(scene)
