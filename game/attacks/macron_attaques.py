# -*- coding: utf-8 -*-
from game.attacks.attack_entity import PersistentAttack
import math
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QColor, QBrush, QPen
from PyQt5.QtCore import Qt
from game.settings import settings


class ProjectGrenade(PersistentAttack):
    def __init__(self, source, direction, x, y):
        super().__init__(
            source=source,
            direction=direction,
            damage=1.0,
            spr_path="enemies/macron/project_grenade", 
            nb_frames=4,
            size=(1, 1),
            pos=(0, 0),
            speed=15 # tiles par seconde
        )
        self.x = x
        self.y = y
        self.anim_speed = 10
        self.do_stun = 0
        self.can_go_on_water = True
        
        self.knockback = 1.5
        self.duree_knockback = 0.3
        
        self.raw_hitbox_data = {
            1: ((1, 12), (14, 9)),
            2: ((1, 12), (14, 9)),
            3: ((1, 12), (14, 9)),
            4: ((1, 12), (14, 9)),
        }
        self.update_hitbox()
        
        
    def check_collisions(self, scene):
        """
        redefinition du check collision pour exclure les murs
        """
        hitbox_zone = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()
        hx, hy = hitbox_zone.x(), hitbox_zone.y()
        hw, hh = hitbox_zone.width(), hitbox_zone.height()
        
        # collision avec bords de l'ecran
        marge = 0 * settings.tile_size
        limit_left = 0 - marge
        limit_right = (16 * settings.tile_size) + marge
        limit_top = (2 * settings.tile_size) - marge
        limit_bottom = (13 * settings.tile_size) + marge
        if (hx < limit_left) or (hx + hw > limit_right) or (hy < limit_top) or (hy + hh > limit_bottom):
            scene.sfx_manager.play(self.die_sfx)
            self.die()
            return
        
        # collision avec ennemis
        for item in scene.items(hitbox_zone):
            if item != self.source and item != self:
                # ignore le switch
                if type(item).__name__ != "CrystalSwitch":
                    # si touche ennemi, disparait
                    if hasattr(item, "take_damage") and item not in self.targets_hit:
                        item.take_damage(scene, self.damage, self)
                        if hasattr(item, "stun"):
                            item.stun(self.do_stun)
                        if hasattr(item, "get_knockback"):
                            item.get_knockback(scene, self)
                        self.targets_hit.add(item)
                        scene.sfx_manager.play(self.die_sfx)
                        self.die() 
                        return


    def die(self):
        if self.scene():
            self.scene().removeItem(self)

class GrenadeMacron(QGraphicsPixmapItem):
    def __init__(self, source, x, y):
        super().__init__()
        self.source = source
        self.x = x
        self.y = y
        self.setZValue(96)

        self.fuse_timer = 3.0
        self.blink_interval = 0.5
        self.blink_timer = 0.0
        self.is_white = False

        self.sprite_normal = QPixmap("assets/enemies/macron/grenade.png").scaled(
            int(settings.tile_size), int(settings.tile_size),
            Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        self.sprite_white = QPixmap("assets/enemies/macron/white_grenade.png").scaled(
            int(settings.tile_size), int(settings.tile_size),
            Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        self.setPixmap(self.sprite_normal)
        self.setPos(self.x, self.y)

    def update(self, dt, scene):
        self.fuse_timer -= dt
        self.blink_timer -= dt

        if self.fuse_timer < 1.0:
            self.blink_interval = 0.15
        elif self.fuse_timer < 2.0:
            self.blink_interval = 0.3

        if self.blink_timer <= 0:
            self.is_white = not self.is_white
            self.setPixmap(self.sprite_white if self.is_white else self.sprite_normal)
            self.blink_timer = self.blink_interval

        if self.fuse_timer <= 0:
            dirs = ["up", "down", "left", "right"]
            for d in dirs:
                proj = ProjectGrenade(self.source, d, self.x, self.y)
                scene.addItem(proj)
                if not hasattr(scene, "projectiles"):
                    scene.projectiles = []
                scene.projectiles.append(proj)
                
            if self.scene():
                self.scene().removeItem(self)

class DalleLumineuse(QGraphicsRectItem):
    def __init__(self, x, y, duration_blink, duration_solid, play_sound=False):
        super().__init__()
        self.x = x
        self.y = y
        self.setRect(0, 0, settings.tile_size, settings.tile_size)
        self.setPos(x, y)
        self.setZValue(10) 
        self.setPen(QPen(Qt.NoPen))
        
        self.timer = 0.0
        self.duration_blink = duration_blink
        self.duration_solid = duration_solid
        self.play_sound = play_sound
        self.state = "blink" 
        self.opacity = 0.0
        self.setBrush(QBrush(QColor(255, 255, 255, 0)))
        self.give_player_knockback = False
        self.knockback = None

    def update(self, dt, scene, macron):
        self.timer += dt
        
        if self.state == "blink":
            progress = self.timer / self.duration_blink
            self.opacity = abs(math.sin(progress * math.pi * 2)) * 150 
            self.setBrush(QBrush(QColor(255, 255, 255, int(self.opacity))))
            
            if self.timer >= self.duration_blink:
                self.state = "solid"
                self.timer = 0.0
                self.setBrush(QBrush(QColor(255, 255, 255, 200)))
                if self.play_sound and hasattr(scene, 'sfx_manager'):
                    scene.sfx_manager.play("snd_dalle_macron")
                    
        elif self.state == "solid":
            
            
            if hasattr(scene, 'player'):

                player_hitbox = scene.player.shrink_hitbox(*scene.player.get_hitbox(),3 * settings.scale)
                
                tile_hitbox = (self.x,self.y,settings.tile_size,settings.tile_size)
                
                if scene.player.rects_overlap(player_hitbox, tile_hitbox):
                    scene.player.take_damage(scene, 0.5, source=macron)
                    
            if self.timer >= self.duration_solid:
                self.state = "fade"
                self.timer = 0.0
                
        elif self.state == "fade":
            progress = self.timer / 0.5
            alpha = max(0, int(200 * (1 - progress)))
            self.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            if self.timer >= 0.5:
                if self.scene():
                    self.scene().removeItem(self)
                return True 
        return False