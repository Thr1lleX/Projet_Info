# -*- coding: utf-8 -*-
from game.attacks.attack_entity import PersistentAttack
from game.settings import settings
from game.config import GRID_WIDTH,GRID_HEIGHT,HUD_HEIGHT

class Trident(PersistentAttack):
    def __init__(self, source, direction, damage, speed):
        super().__init__(
            source=source,
            direction=direction,
            damage=damage,
            spr_path="enemies/poseidon/trident",
            nb_frames=1,
            size=(1, 2),
            pos=(0, 0),
            speed=speed # tiles par seconde
        )
        self.anim_speed = 0 # 0 car 1 seule frame
        self.do_stun = 0
        self.can_go_on_water = True
        self.die_sfx = None
        
        # Hitbox fournie
        self.raw_hitbox_data = {
            1: ((3, 0), (13, 14))
        }
        self.update_hitbox()

    def check_collisions(self, scene):
        hitbox_zone = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()
        hx, hy = hitbox_zone.x(), hitbox_zone.y()
        hw, hh = hitbox_zone.width(), hitbox_zone.height()
        
        # Collision avec bords de l'ecran avec une marge de 2 tuiles pour qu'il sorte bien
        marge = 2 * settings.tile_size
        limit_left = 0 - marge
        limit_right = (GRID_WIDTH * settings.tile_size) + marge
        limit_top = (0 * settings.tile_size) - marge # On peut spawner de plus haut
        limit_bottom = ((GRID_HEIGHT+HUD_HEIGHT) * settings.tile_size) + marge
        
        if (hx < limit_left) or (hx + hw > limit_right) or (hy < limit_top) or (hy + hh > limit_bottom):
            self.die()
            return
        
        # Collisions UNIQUEMENT avec les entites (ignorer murs et decors)
        for item in scene.items(hitbox_zone):
            if item != self.source and item != self:
                if hasattr(item, "take_damage") and item not in self.targets_hit:
                    item.take_damage(scene, self.damage, self)
                    item.stun(self.do_stun)
                    self.targets_hit.add(item)
                    self.die() 
                    return

    def die(self):
        if self.scene():
            self.scene().removeItem(self)   