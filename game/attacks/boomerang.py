# -*- coding: utf-8 -*-

from game.attacks.attack_entity import PersistentAttack
from game.config import TILE_SIZE

class Boomerang(PersistentAttack):
    def __init__(self, source, direction):
        super().__init__(
            source=source,
            direction=direction,
            damage=0,
            spr_path="player/attack/boomerang", 
            nb_frames=8,
            size=(1, 1),
            pos=(0, 0),
            speed=7
        )
        
        self.only_one = True
        
        self.anim_speed = 7
        self.do_stun = 3
        
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
        
        self.update_hitbox()

    def die(self):
        if self.scene():
            self.scene().removeItem(self)
