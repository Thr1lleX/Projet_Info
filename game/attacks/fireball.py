# -*- coding: utf-8 -*-
from game.attacks.attack_entity import PersistentAttack
from game.enemies.enemy import Enemy 

class Fireball(PersistentAttack):
    """Projectile de type boule de feu (utilisable par le joueur et les ennemis)."""
    def __init__(self, source, direction):
        if isinstance(source, Enemy):
            img_spr = "enemies/wizmount/fireball"
            damage = 3
        else:
            img_spr = "player/attack/fireball"
            damage = 2
        super().__init__(
            source=source,
            direction=direction,
            damage=damage,
            spr_path=img_spr, 
            nb_frames=4,
            size=(1, 1),
            pos=(0, 0),
            speed=12.5 # tiles par seconde
        )
        self.anim_speed = 10
        self.do_stun = 0
        self.can_go_on_water = True
        self.die_sfx = "snd_fire_die"
        
        self.raw_hitbox_data = {
            1: ((3, 0), (13, 15)),
            2: ((3, 0), (13, 15)),
            3: ((3, 0), (13, 15)),
            4: ((3, 0), (13, 15)),
        }
        self.update_hitbox()

    def die(self):
        """Supprime le projectile sans effet d'explosion special."""
        if self.scene():
            self.scene().removeItem(self)
