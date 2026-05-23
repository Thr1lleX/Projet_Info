# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsLineItem
from PyQt5.QtCore import Qt

from game.entity import Entity
from game.config import DEBUG, HUD_HEIGHT
from game.pathfinder import astar, get_walkable_grid
import math
import random
from game.dropped_item import DroppedItem

from game.settings import settings

class Enemy(Entity):
    def __init__(self, scale, x, y):
        super().__init__(scale)

        self.x = x
        self.y = y
        
        self.speed = settings.base_speed

        # cible par defaut
        self.target = None

        # portée détection standard
        self.aggro_range = settings.tile_size * 13
        
        self.damage = 1 #degats de base
        self.give_stun = 0 # duree du stun infligé au joueur (0 = pas de stun)
        
        self.recoil_distance = 0.5 #distance qu'ils recoient lorsquent frappent joueur
        
        # loot
        self.loot = [
            ("pomme",  0.10),
            ("potion", 0.10),
            ("bombe",  0.10)
        ]


        # Pathfinding
        self.use_pathfinding = True
        self.path = []
        self.path_timer = 0.0
        self.path_interval = 0.05
        self.show_path = DEBUG
        self.path_rects = []
        self.path_lines = []


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
            if DEBUG:
                self.draw_debug_path(scene)
            return
        
        #ensuite prio stun, comme pour player
        if self.is_stunned:
            self.apply_stun_wiggle(dt,scene)
            self.update_graphics()
            self.update_damage_state(dt)
            self.update_stun_animation(dt)
            if DEBUG:
                self.draw_debug_path(scene)
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

        if self.use_pathfinding:
            self.path_timer += dt
            if self.path_timer >= self.path_interval:
                self.path_timer = 0.0
                
                # On calcule les dimensions en tuiles séparément
                w_tiles = max(1, math.ceil(self.hitbox_width / settings.tile_size))
                h_tiles = max(1, math.ceil(self.hitbox_height / settings.tile_size))
                
                start_pos = start_pos = (self.x + settings.tile_size / 2.0, self.y + settings.tile_size / 2.0)
                goal_pos = (self.target.x + settings.tile_size / 2.0, self.target.y + settings.tile_size / 2.0)
                
                grid = get_walkable_grid(scene.room_data)
                
                # On passe les deux dimensions
                new_path = astar(grid, start_pos, goal_pos, settings.tile_size, w_tiles, h_tiles)
                
                
                if new_path is not None:
                    self.path = new_path
                else:
                    self.path = []
                    
                if self.show_path:
                    self.draw_debug_path(scene)

            if self.path:
                next_pos = self.path[0]
                target_x = next_pos[0]
                target_y = next_pos[1]
                
                # Cible par rapport au CENTRE de l'ennemi
                center_x = self.x + settings.tile_size / 2.0
                center_y = self.y + settings.tile_size / 2.0
                
                dx = target_x - center_x
                dy = target_y - center_y
                
                dist_to_next = (dx**2 + dy**2) ** 0.5
                
                if dist_to_next < self.speed * dt:
                    self.path.pop(0)
                    if self.path:
                        next_pos = self.path[0]
                        target_x = next_pos[0]
                        target_y = next_pos[1]
                        dx = target_x - center_x
                        dy = target_y - center_y
                        dist_to_next = (dx**2 + dy**2) ** 0.5

                if dist_to_next > 0:
                    dx /= dist_to_next
                    dy /= dist_to_next
            else:
                if dist > 0:
                    dx /= dist
                    dy /= dist
        else:
            if dist > 0:
                dx /= dist
                dy /= dist

        if dx != 0 or dy != 0:
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

        self.move(dx, dy, dt, scene)
        self.update_graphics()
        self.update_stun_animation(dt)
        self.update_damage_state(dt)
        
        self.try_hit_player(scene)

    def die(self):
        scene = self.scene()
    
        if scene:
            # On verifie si ennemi a flag a declencher (defini dans spawn enemy)
            if hasattr(self, "set_flag_on_death") and self.set_flag_on_death:
                if hasattr(scene, "session_flags"):
                    flag_data = self.set_flag_on_death
                    # on transforme en liste si c'est un string pour boucler dessus (gestion de plusieurs flags)
                    flags = [flag_data] if isinstance(flag_data, str) else flag_data
                    
                    for f in flags:
                        #scene.current_save.set_flag(f)
                        scene.session_flags[f] = True
                        if DEBUG: print(f"[ENEMY] Flag de session déclenché à la mort : {f}")                                                                          
            # Nettoyer les chemins de debug
            if self.path_rects:
                for rect in self.path_rects:
                    if rect.scene() == scene:
                        scene.removeItem(rect)
                self.path_rects.clear()
                
                for line in self.path_lines:
                    if line.scene() == scene:
                        scene.removeItem(line)
                self.path_lines.clear()
    
            room = self.room_name
    
            if room not in scene.room_states:
                scene.room_states[room] = {
                    "killed_enemies": set()
                }
    
            scene.room_states[room]["killed_enemies"].add(self.enemy_id)
        self._drop_loot(scene)

        super().die()

# drop loot        
    def _drop_loot(self,scene):
        offset = int(0.3 * settings.tile_size)
        for item_id, chance in self.loot:
            if random.random() < chance:
                dx = random.randint(-offset, offset)
                dy = random.randint(-offset, offset)
                drop = DroppedItem(item_id, self.x + dx , self.y + dy)
                scene.addItem(drop)
                scene.dropped_items.append(drop)
        
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
                
            old_player_kb = self.target.knockback
            self.target.knockback = self.recoil_distance
            
            self.get_knockback(scene, self.target)
            
            self.target.knockback = old_player_kb

    def draw_debug_path(self, scene):
        # Clear old items
        for item in self.path_rects + self.path_lines:
            if item.scene() == scene:
                scene.removeItem(item)
        self.path_rects.clear()
        self.path_lines.clear()

        if not self.path:
            return

        # Use centers for visualization
        current_x = self.x + settings.tile_size / 2
        current_y = self.y + settings.tile_size / 2

        for px, py in self.path:
            # Red line connecting waypoints
            line = QGraphicsLineItem(current_x, current_y, px, py)
            line.setPen(QPen(QColor(255, 0, 0, 180), 2))
            line.setZValue(84)
            scene.addItem(line)
            self.path_lines.append(line)

            # Green waypoint markers
            rect = QGraphicsRectItem(
                px - 4,
                py - 4,
                8,
                8
            )
            rect.setBrush(QBrush(QColor(0, 255, 0, 200)))
            rect.setPen(QPen(Qt.NoPen))
            rect.setZValue(85)
            scene.addItem(rect)
            self.path_rects.append(rect)

            # Update current to next point
            current_x, current_y = px, py
            
        
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