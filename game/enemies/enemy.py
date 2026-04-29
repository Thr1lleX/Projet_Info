# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPen, QColor

from game.entity import Entity
from game.config import BASE_SPEED, DEBUG

class Enemy(Entity):
    def __init__(self, scale, x, y):
        super().__init__(scale)

        self.x = x
        self.y = y
        
        self.speed = BASE_SPEED

        # cible par defaut
        self.target = None

        # portée détection standard
        self.aggro_range = self.tile_size * 7
        
        self.damage = 1 #degats de base
        self.give_stun = 0 # duree du stun infligé au joueur (0 = pas de stun)


        if DEBUG:
            self.debug_rect.setPen(QPen(QColor("red"), 1))

    def set_target(self, target):
        self.target = target

    def update(self, dt, scene):
        
        # priorite knockback pour bloquer mvmt
        if self.kb_active:
            self.apply_knockback(dt, scene)
            self.update_graphics()
            self.update_damage_state(dt)
            return
        
        #ensuite prio stun, comme pour player
        if self.is_stunned:
            self.apply_stun_wiggle(dt,scene)
            self.update_graphics()
            self.update_damage_state(dt)
            return

        if not self.target:
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y

        dist = (dx**2 + dy**2) ** 0.5

        # joueur trop loin
        if dist > self.aggro_range:
            self.update_graphics()
            self.update_damage_state(dt)
            return

        if dist > 0:
            dx /= dist
            dy /= dist

            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

        self.move(dx, dy, dt, scene)
        self.update_graphics()
        
        self.update_damage_state(dt)
        
        self.try_hit_player(scene)

    def die(self):
        scene = self.scene()
    
        if scene:
    
            room = self.room_name
    
            if room not in scene.room_states:
                scene.room_states[room] = {
                    "killed_enemies": set()
                }
    
            scene.room_states[room]["killed_enemies"].add(self.enemy_id)
    
        super().die()
        
    def try_hit_player(self,scene):
        #n'attque que cible et peut pas attquer si stun
        if not self.target or self.is_stunned:
            return
    
        ex, ey, ew, eh = self.get_hitbox()
        px, py, pw, ph = self.target.get_hitbox()
    
        collision = (
            ex < px + pw and
            ex + ew > px and
            ey < py + ph and
            ey + eh > py
        )
    
        if collision:
            self.target.take_damage(scene, self.damage, self)
            #self.target.stun(self.give_stun, wiggle=True)
            if self.give_stun > 0: 
                # on doit additionner les temps car ils demarrent tout deux au coup
                self.target.stun(self.give_stun+self.duree_knockback, wiggle=True)
            
        
"""
selon type d'entite redefinir
ennemie random 
def die(self):
    drop_gold()
    super().die()

boss 
def die(self):
    open_door()
    play_animation()
    
joueur 
def die(self):
    game_over()
"""