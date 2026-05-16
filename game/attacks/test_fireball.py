# -*- coding: utf-8 -*-
from game.attacks.attack_entity import PersistentAttack

class Fireball(PersistentAttack):
    def __init__(self, source, direction):
        super().__init__(
            source=source,
            direction=direction,
            damage=2,
            spr_path="player/attack/fireball", 
            nb_frames=5,
            size=(1, 1),
            pos=(0, 0),
            speed=10.0 # tiles par seconde
        )
        self.anim_speed = 0.08
        self.do_stun = 0
        
        self.raw_hitbox_data = {
            1: ((4, 4), (12, 12)),
            2: ((4, 4), (12, 12)),
            3: ((4, 4), (12, 12)),
            4: ((4, 4), (12, 12)),
        }
        self.update_hitbox()

    def die(self):
        if self.scene():
            self.scene().removeItem(self)
