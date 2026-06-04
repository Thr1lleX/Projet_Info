# # -*- coding: utf-8 -*-
# from game.attacks.attack_entity import PersistentAttack
# from game.settings import settings
# from game.config import GRID_WIDTH,GRID_HEIGHT,HUD_HEIGHT

# class Trident(PersistentAttack):
#     def __init__(self, source, direction, damage, speed):
#         super().__init__(
#             source=source,
#             direction=direction,
#             damage=damage,
#             spr_path="enemies/poseidon/trident",
#             nb_frames=1,
#             size=(1, 2),
#             pos=(0, 0),
#             speed=speed # tiles par seconde
#         )
#         self.anim_speed = 0 # 0 car 1 seule frame
#         self.do_stun = 0
#         self.can_go_on_water = True
#         self.die_sfx = None
        
#         # Hitbox fournie
#         self.raw_hitbox_data = {
#             1: ((3, 0), (13, 14))
#         }
#         self.update_hitbox()

#     def check_collisions(self, scene):
#         hitbox_zone = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()
#         hx, hy = hitbox_zone.x(), hitbox_zone.y()
#         hw, hh = hitbox_zone.width(), hitbox_zone.height()
        
#         # Collision avec bords de l'ecran avec une marge de 2 tuiles pour qu'il sorte bien
#         marge = 2 * settings.tile_size
#         limit_left = 0 - marge
#         limit_right = (GRID_WIDTH * settings.tile_size) + marge
#         limit_top = (0 * settings.tile_size) - marge # On peut spawner de plus haut
#         limit_bottom = ((GRID_HEIGHT+HUD_HEIGHT) * settings.tile_size) + marge
        
#         if (hx < limit_left) or (hx + hw > limit_right) or (hy < limit_top) or (hy + hh > limit_bottom):
#             self.die()
#             return
        
#         # Collisions UNIQUEMENT avec les entites (ignorer murs et decors)
#         for item in scene.items(hitbox_zone):
#             if item != self.source and item != self:
#                 if hasattr(item, "take_damage") and item not in self.targets_hit:
#                     item.take_damage(scene, self.damage, self)
#                     item.stun(self.do_stun)
#                     self.targets_hit.add(item)
#                     self.die() 
#                     return

#     def die(self):
#         if self.scene():
#             self.scene().removeItem(self)   

# -*- coding: utf-8 -*-
import math
from game.attacks.attack_entity import PersistentAttack
from game.settings import settings
from game.config import GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT

class Trident(PersistentAttack):
    def __init__(self, source, direction, damage, speed, target=None):
        super().__init__(
            source=source,
            direction=direction,
            damage=damage,
            spr_path="enemies/poseidon/trident",
            nb_frames=1,
            size=(1, 2),
            pos=(0, 0),
            speed=speed
        )
        self.anim_speed = 0
        self.do_stun = 0
        self.can_go_on_water = True
        self.die_sfx = None
        
        # --- SYSTÈME DE SUIVI ---
        self.target = target
        self.tracking_duration = 0.75
        self.tracking_timer = self.tracking_duration
        self.turn_speed = 2.75  # Force du virage 

        # On stocke l'angle de la direction cardinale de depart
        direction_angles = {"right": 0, "down": math.pi/2, "left": math.pi, "up": -math.pi/2}
        self.initial_angle = direction_angles.get(direction, 0)
        self.angle = self.initial_angle
        
        # Centre de rotation base sur le pixmap reel
        rect = self.pixmap().rect()
        self.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)

        # Hitbox d'origine (laissee a la charge de la rotation de la classe mere)
        self.raw_hitbox_data = {
            1: ((3, 0), (13, 14))
        }
        self.update_hitbox()

    def update_position(self):
        rect = self.pixmap().rect()
        
        if self.target and self.tracking_timer > 0:
            self.tracking_timer -= self.current_dt
            
            # centre absolu du Trident dans le monde
            cx = self.x + rect.width() / 2
            cy = self.y + rect.height() / 2
            
            # position absolue de la pointe du trident
            # On la projette vers l'avant depuis le centre, dans l'axe de self.angle
            dist_to_tip = max(rect.width(), rect.height()) / 2
            pointe_x = cx + math.cos(self.angle) * dist_to_tip
            pointe_y = cy + math.sin(self.angle) * dist_to_tip
            
            # angle idéal vers le milieu de la cible
            tx, ty = self.target.get_center()
            target_angle = math.atan2(ty - pointe_y, tx - pointe_x)
            
            # difference d'angle la plus courte (normalisée entre -pi et pi)
            diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            
            # adoucissement par courbe sinusoidale
            tracking_ratio = max(0, self.tracking_timer / self.tracking_duration)
            smooth_factor = math.sin(tracking_ratio * (math.pi / 2))
            
            # applique deviation sur l'angle absolu
            self.angle += diff * smooth_factor * self.turn_speed * self.current_dt

        # deplacement continu base sur l'angle absolu actuel
        move_dist = self.projectile_speed * settings.tile_size * self.current_dt
        self.x += math.cos(self.angle) * move_dist
        self.y += math.sin(self.angle) * move_dist
        
        self.setPos(self.x + self.anim_offset[0], self.y + self.anim_offset[1])
        
        # on calcule uniquement la deviation par rapport à l'orientation de depart
        relative_angle = self.angle - self.initial_angle
        rotation_deg = math.degrees(relative_angle)
        
        # avec rotation relative, Qt se charge de faire tourner le sprite et et debug_rect enfant synchronisee
        self.setRotation(rotation_deg)
        
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
