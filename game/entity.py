# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QPen, QColor, QPainter
from PyQt5.QtCore import Qt
from abc import abstractmethod

from game.config import BASE_TILE_SIZE, DEBUG, BASE_SPEED, GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, HUD_HEIGHT
import random

class Entity(QGraphicsPixmapItem):
    def __init__(self, scale):
        super().__init__()

        self.setZValue(90)
        self.scale = scale
        self.tile_size = BASE_TILE_SIZE * scale

        # --- POSITION --- (float, la position est pixel en haut à gauche)
        self.x = 0
        self.y = 0

        # --- STATS ---
        self.pv_max = 1
        self.pv_main = 1
        self.speed = 0
        self.is_damaged = False
        
        # -- Damages---
        self.is_damaged = False
        self.damage_timer = 0
        self.damage_duration = 0.15
        self._base_sprites = {}
        
        # -- Invulnérabilite et effst
        self.is_invulnerable = False
        self.invuln_timer = 0
        self.invuln_duration = 0.30
        
        self.is_effect_immune = False   # stun / kb ...
        self.effect_immunity_timer = 0
        self.effect_immunity_duration = 0
        
        # -- Attaques
        self.attack_cooldown = 0
        self.attack_delay = 0.25
        self.knockback = 1 # knockback inflige a l'ennemoi lorsque qu'attaque 
        
        # parametres de base de knockback, a pas changer 
        self.duree_knockback = 0.15
        self.kb_active = False
        
        # -- STun--
        self.is_stunned = False
        self.stun_timer = 0
        self.stun_duration = 0
        #self.stun_wiggle_duration = 0
        
        self.enable_stun_wiggle = False # random initialisation, change rien

        # --- COLLISION ---
        self.collision = 1

        # --- HITBOX ---
        self.hitbox_offset_x = 0
        self.hitbox_offset_y = 0
        self.hitbox_width = self.tile_size
        self.hitbox_height = self.tile_size
        
        

        # --- SPRITES ---
        base_sprite = QPixmap("assets/entity.png").scaled(
            self.tile_size,
            self.tile_size,
            transformMode=Qt.FastTransformation
        )

        self.sprites = {
            "down": base_sprite,
            "up": base_sprite,
            "left": base_sprite,
            "right": base_sprite
        }

        self.direction = "down"
        
        # -- CRIS DE DEGATS
        
        self.cries = []
        self.death_cry = "snd_placeholderdeath"

        # --- DEBUG ---
        if DEBUG:
            self.debug_rect = QGraphicsRectItem(self)
            self.debug_rect.setZValue(999)

    def get_hitbox(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y

        return (
            x + self.hitbox_offset_x * self.tile_size,
            y + self.hitbox_offset_y * self.tile_size,
            self.hitbox_width,
            self.hitbox_height
        )

    def get_center(self):
        x, y, w, h = self.get_hitbox()
        return (x+w/2,y+h/2)

    # def clamp_to_room_bounds(self, scene, x, y):
    #     """
    #     empecher entites de traverser bounds ()
    #     """
    #     room_w = scene.sceneRect().width()
    #     room_h = scene.sceneRect().height()
    
    #     # hitbox actuelle
    #     _, _, w, h = self.get_hitbox(x, y)
    
    #     x = max(0, min(x, room_w - w))
    #     y = max(0, min(y, room_h - h))
    
        return x, y    

    def move(self, dx, dy, dt, scene):
        new_x = self.x + dx * self.speed * dt
        new_y = self.y + dy * self.speed * dt
        # --- collision par rapport a hitbox
        if self.collision:
            hx, hy, hw, hh = self.get_hitbox(new_x, self.y)
            if not scene.is_blocking_rect(hx, hy, hw, hh):
                self.x = new_x

            hx, hy, hw, hh = self.get_hitbox(self.x, new_y)
            if not scene.is_blocking_rect(hx, hy, hw, hh):
                self.y = new_y
        else:
            self.x = new_x
            self.y = new_y

    def take_damage(self, scene, damage, source=None):
        """
        on a 4 points
        1 invulnerabilite pour pas se faire enchainer
        2 les degats pris, retire pv par rapport a damage et mets invulnerable
        3 knockback, on prend les centres de hitbox, et recule de x tiles dans vecteur oppose
        4 la mort
        """
        if self.is_invulnerable:
            return 
        
        self.pv_main -= damage
        if self.cries and self.pv_main > 0: #jouer un cri aleatoire parmi liste de cris, en general 2
            scene.sfx_manager.play(random.choice(self.cries))

        if DEBUG:
            class_name = self.__class__.__name__
            print(f"[{class_name.upper()} HP] : {self.pv_main}/{self.pv_max}")
    
        # les degats aie j'ai mal
        self.is_damaged = True
        self.damage_timer = 0
        
        self.is_invulnerable = True
        self.invuln_timer = 0
        
        self.apply_red_flash()
    
        # knockback
        self.get_knockback(scene,source)

        # la mort huhuhuhuuuu
        if self.pv_main <= 0:
            scene.sfx_manager.play(self.death_cry)
            self.die()
        
    def die(self):
        scene = self.scene()
        if scene:
            # retirer de la liste ennemis si besoin
            if hasattr(scene, "enemies") and self in scene.enemies:
                scene.enemies.remove(self)
            # supprimer hitbox debug
            if hasattr(self, "debug_rect"):
                scene.removeItem(self.debug_rect)
        self.setVisible(False)

    def apply_red_flash(self):
        """
        Fonction pour declencher effet visuel de degats
        """
        # sauvegarde des sprites originaux si n'existent pas
        if not self._base_sprites:
            self._base_sprites = self.sprites.copy()

        # --- effet rouge simple --- seulement par dessus pixels non transparents

        for key in self.sprites:
            original = self._base_sprites[key]
    
            # copie du sprite
            tinted = original.copy()
    
            painter = QPainter(tinted)
    
            # applique rouge uniquement sur pixels visibles
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(
                tinted.rect(),
                QColor(255, 0, 0, 120)
            )
    
            painter.end()
    
            self.sprites[key] = tinted
    
    def get_knockback(self, scene, source=None):
        """
        CETTE FONCITON EST APPELEE LORSQUE C'EST L'ASSAILLANT QUI RECOIT RECUL APRES COUP!!!
        
        Fonction utilisee dans take_damage, mais cree ici a part car besoin de l'invoquer
        lorsque entite qui frappe n'inflige pas de degats. 
        Donc pouvoir recevoir recul sans take_damage
        
        Fonctionnement: on prend les centres de hitbox, et recule de x tiles dans vecteur oppose
        """
        # knockback
        if source is not None:
            sx, sy = source.get_center()
            tx, ty = self.get_center()
    
            dx = tx - sx
            dy = ty - sy
    
            dist = (dx**2 + dy**2) ** 0.5
    
            if dist > 0:
                dx /= dist
                dy /= dist
    
                # on utilise le knockback de l'assaillant en pixels
                distance = source.knockback * self.tile_size
                
                
                self.kb_dir_x = dx
                self.kb_dir_y = dy
                
                self.kb_remaining = distance
                self.kb_speed = distance / source.duree_knockback
                
                self.kb_active = True

    def apply_knockback(self, dt, scene):
        """
        CETTE FONCITON EST APPELEE LORSQUE C'EST L'ASSAILLANT QUI INFLINGE RECUL A L'ENNEMI!!!
        
        Fonciton qui va bouger petit a petit le joueur 
        dans direction du knockback, en fonction de kb_speed
        
        On fait petit a petit, pour transition, 
        et on bloque mouvement par _move_with_collision_limit
        """
        if not self.kb_active:
            return
    
        move_step = self.kb_speed * dt
    
        # pas depasser distance totale
        if move_step > self.kb_remaining:
            move_step = self.kb_remaining
    
        dx = self.kb_dir_x * move_step
        dy = self.kb_dir_y * move_step
    
        self._move_with_collision_limit("x", dx)
        self._move_with_collision_limit("y", dy)
    
        self.kb_remaining -= move_step
    
        if self.kb_remaining <= 0:
            self.kb_active = False
        
                
    def _move_with_collision_limit(self, axis, amount):
        """
        deplace sur un axe en appliquand deplcement max autorise
        axis : "x" ou "y"
        amount : déplacement en pixels (float)
        """
        if amount == 0:
            return
    
        steps = int(abs(amount))
        direction = 1 if amount > 0 else -1
    
        # deplacement pixel par pixelcar si d'un coup foncitonne pas
        for _ in range(steps):
            if axis == "x":
                test_x = self.x + direction
                hx, hy, hw, hh = self.get_hitbox(test_x, self.y)
                
                #bloquer le deplcament si collision
                if self.scene().is_blocking_rect(hx, hy, hw, hh):
                    return
                
                #bloquer le deplacement si oob
                if self._is_out_of_bounds(test_x, self.y):
                    return
    
                self.x = test_x
    
            else:
                test_y = self.y + direction
                hx, hy, hw, hh = self.get_hitbox(self.x, test_y)
    
                if self.scene().is_blocking_rect(hx, hy, hw, hh):
                    return
                
                if self._is_out_of_bounds(self.x,test_y):
                    return
    
                self.y = test_y

        rest = abs(amount) - steps
        if rest <= 0:
            return
        
        # avec le reste
        if axis == "x":
            test_x = self.x + direction * rest
            hx, hy, hw, hh = self.get_hitbox(test_x, self.y)
    
            if not self.scene().is_blocking_rect(hx, hy, hw, hh) and not self._is_out_of_bounds(test_x, self.y):
                self.x = test_x
    
        else:
            test_y = self.y + direction * rest
            hx, hy, hw, hh = self.get_hitbox(self.x, test_y)
    
            if not self.scene().is_blocking_rect(hx, hy, hw, hh) and not self._is_out_of_bounds(self.x,test_y):
                self.y = test_y

    def _is_out_of_bounds(self, x, y):
        scene = self.scene()
        if not scene:
            return False
    
        w = GRID_WIDTH * TILE_SIZE
        h = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE
    
        hx, hy, hw, hh = self.get_hitbox(x, y)
    
        return (
            hx < 0 or
            hy < HUD_HEIGHT * TILE_SIZE or
            hx + hw > w or
            hy + hh > h
        )
    



    def update_graphics(self):
        """
        affiche joeur et hitbox
        """
        self.setPixmap(self.sprites[self.direction])
        self.setPos(self.x, self.y)
        
        if hasattr(self, "debug_rect"): #activer hitboxes
            # hx, hy, hw, hh = self.get_hitbox()
            # self.debug_rect.setRect(hx, hy, hw, hh)
            hx, hy, hw, hh = self.get_hitbox()
            
            self.debug_rect.setRect(
                hx - self.x,
                hy - self.y,
                hw,
                hh
            )
    def update_damage_state(self, dt):
        """
        Fonction qui permet de mettre l'effect rouge lorsque degat prit
        et qui maintenant gere le stun mdr
        """
        # degats flash rouge
        if self.is_damaged:
            self.damage_timer += dt
    
            if self.damage_timer >= self.damage_duration:
                self.is_damaged = False
    
                # restore sprites
                if self._base_sprites:
                    self.sprites = self._base_sprites.copy()
        
        # invulnerabilite
        if self.is_invulnerable:
            self.invuln_timer += dt
    
            if self.invuln_timer >= self.invuln_duration:
                self.is_invulnerable = False
        
        # -- immunite aux effets
        if self.is_effect_immune:
            self.effect_immunity_timer += dt
            if self.effect_immunity_timer >= self.effect_immunity_duration:
                 self.is_effect_immune = False
                 self.effect_immunity_timer = 0
        
        # --- STUN ---
        if self.is_stunned:
            self.stun_timer += dt
        
            if self.stun_timer >= self.stun_duration:
                self.is_stunned = False
                self.stun_timer = 0

    def apply_stun_wiggle(self, dt, scene):
        """
        C'est juste un truc qui fait wiggle quoi
        """
        if not self.is_stunned or not self.enable_stun_wiggle:
            return
        if self.stun_wiggle_duration <= 0:
            return
    
        self.stun_wiggle_timer += dt
    
        t = self.stun_wiggle_timer / self.stun_wiggle_duration
    
        if t > 1:
            return
    
        # en divise mvnt en 3 phases : 0.1 -> -0.2 -> 0.1
        #dist_wiggle = 0.1 # parametre de distance wiggle
        A = 0.05 # parametre de distance wiggle
        if t < 0.33:
            offset = (t / 0.33) * A
        elif t < 0.66:
            offset = A - ((t - 0.33) / 0.33) * (3*A)
        else:
            offset = -2*A + ((t - 0.66) / 0.34) * (3*A)
    
        offset_pixels = offset * self.tile_size
    
        dx = self.stun_perp_x * offset_pixels
        dy = self.stun_perp_y * offset_pixels
        
        # pour pas aller dans murs
        self._move_with_collision_limit("x", dx)
        self._move_with_collision_limit("y", dy)


    @abstractmethod
    def update(self, dt, scene):
        pass
    
    ### EFFETS, ON AJOUTE UN COOLDOWN D'INVULERABILITE
    
    def stun(self, duration, wiggle=True):
        """
        applique un stun pendant 'duration' s
        
        stun empeche de bouger, d'attaquer et fait un petit mvt
        """
        # empeche l'application de stun a ennemi invulnerable aux effets
        if self.is_effect_immune:
            return 
        
        # # si ennemi deja stun, on garde le stun le plus long (pour enchainer coups)
        # if self.is_stunned:
        #     self.stun_duration = max(self.stun_duration, duration)
        #     return
    
        self.is_stunned = True
        self.stun_timer = 0
        self.stun_duration = duration
        
        self.is_effect_immune = True
        self.effect_immunity_timer = 0
        
        # on ajoute un petit wiggle parce que joli
        self.enable_stun_wiggle = wiggle
        if not wiggle or duration <= 0:
            self.stun_wiggle_duration = 0
            return
    
        self.stun_wiggle_timer = 0
        self.stun_wiggle_duration = min(0.1, duration)
    
        # direction du vecteur perpendiculaire
        self.stun_perp_x = -self.kb_dir_y
        self.stun_perp_y = self.kb_dir_x