# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.config import BASE_TILE_SIZE, HUD_HEIGHT
from game.attacks.attack_entity import TemporaryAttack
from game.animspr import load_animation_sequence

from game.settings import settings

class Bomb(QGraphicsPixmapItem):
    """
    gere uniquement la bombe posee au son, son timer et son clignetement
    cette entite n'a ni hitbox ni degats
    """
    def __init__(self, source, x, y):
        super().__init__()
        self.source = source
        self.x = x
        self.y = y
        
        self.setZValue(96)

        self.total_fuse = 4.0
        self.fuse_timer = self.total_fuse
        
        # on commence clignotement tous les 0.5s puis accelere
        self.initial_blink_interval = 0.5
        self.blink_timer = 0.0
        self.blink_interval = self.initial_blink_interval
        
        self.is_white = False

        # --- SPRITES ---
        self.sprite_normal = QPixmap("assets/player/attack/bombe.png").scaled(
            int(settings.tile_size * 0.75),
            int(settings.tile_size * 0.75),
            Qt.IgnoreAspectRatio,
            Qt.FastTransformation
        )
        self.sprite_white = QPixmap("assets/player/attack/white_bombe.png").scaled(
            int(settings.tile_size * 0.75),
            int(settings.tile_size * 0.75),
            Qt.IgnoreAspectRatio,
            Qt.FastTransformation
        )

        self.setPixmap(self.sprite_normal)

        offset_center = (settings.tile_size - int(settings.tile_size * 0.75)) / 2
        self.setPos(self.x + offset_center, self.y + offset_center)

    def update(self, dt, scene):
        self.fuse_timer -= dt
        self.blink_timer += dt
        
        elapsed_time = self.total_fuse - self.fuse_timer
        
        # coefficient pr accelerer plus ou moins vite
        reduction_factor = 0.15
        self.blink_interval = max(self.initial_blink_interval - (elapsed_time * reduction_factor), 0.075)

        # Logique de clignotement
        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0 # On reset le timer de clignotement
            self.is_white = not self.is_white
            self.setPixmap(self.sprite_white if self.is_white else self.sprite_normal)

        #` fin du timer on declenche explosion
        if self.fuse_timer <= 0:
            self.explode(scene)

    def explode(self, scene):
        """
        invoque attaque explosion et clean la bombe
        """
        explosion = Explosion(self.source, self.x, self.y)
        scene.addItem(explosion)
        
        # on ajoute l'explosion à la liste des projectiles pour que la scène fasse son update()
        self.source.projectiles.append(explosion)

        # Jouer le son d'explosion si besoin
        scene.sfx_manager.play("snd_explosion")

        self.die()

    def die(self):
        if self.scene():
            self.scene().removeItem(self)


class Explosion(TemporaryAttack):
    """
    herite de temporary attack (voir def de classe)
    3x3, centre en (1,1)
    """
    def __init__(self, source, x, y):
        # on force down pour la direction meme si pas d'importance
        super().__init__(source, direction="down", damage=2, duration=0.8)
        self.setZValue(99)

        self.x = x
        self.y = y

        self.spr = "player/attack/explosion"
        self.size = (3, 3)
        self.pos_origin = (1, 1)
        self.nb_frames = 8

        self.frames = load_animation_sequence(f"assets/{self.spr}", self.size, self.nb_frames)
        self.anim_speed = self.duration / len(self.frames)
        self.setPixmap(self.frames[0])

        self.anim_offset = (
            -self.pos_origin[0] * settings.tile_size,
            -self.pos_origin[1] * settings.tile_size
        )
        self.raw_hitbox_data = {
            1: ((19, 29), (30, 17)),
            2: ((13, 34), (36, 12)),
            3: ((13, 34), (36, 13)),
            4: ((19, 29), (28, 24)),
            5: ((0, 0), (0, 0)),
            6: ((0, 0), (0, 0)),
            7: ((0, 0), (0, 0)),
            8: ((0, 0), (0, 0))
        }
        
        self.can_hit_source = True
        
        center_tile_x = int(x // settings.tile_size)
        center_tile_y = int((y - HUD_HEIGHT * settings.tile_size) // settings.tile_size)

        # On vérifie un carré de 3x3 autour du centre
        if source.scene(): # Sécurité pour accéder à la scène
            scene = source.scene()
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    scene.try_break_tile(center_tile_x + dx, center_tile_y + dy)

        self.update_hitbox()
        self.update_position()


    def die(self):
        if self.scene():
            self.scene().removeItem(self)
