# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QPen, QColor, QPainter
from PyQt5.QtCore import Qt
from abc import abstractmethod

from game.config import BASE_TILE_SIZE, DEBUG, BASE_SPEED, GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, HUD_HEIGHT
from game.animspr import load_animation_sequence
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

        # --- STATS --- (on peut avoir des pv non entiers)
        self._pv_max = 1
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

        # -- CORRECTIONS COIN --
        self.corner_correction = True

        # --- HITBOX ---
        self.hitbox_offset_x = 0
        self.hitbox_offset_y = 0
        self.hitbox_width = self.tile_size
        self.hitbox_height = self.tile_size
        
        self.stun_perp_x = 0
        self.stun_perp_y = 0

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

        self.can_go_on_water = False
        
        
        # --- STUN ANIMATION'---
        self.stun_frames = load_animation_sequence(
            "assets/effects/stunanim",
            size=(1, 2)
        )
        
        self.stun_frame_index = 0
        self.stun_anim_speed = 10
        self.stun_anim_timer = 0
        
        self.stun_item = QGraphicsPixmapItem(self)
        self.stun_item.setZValue(200)
        self.stun_item.setVisible(False)
        
        
        # --- BUFF ANIMATION --- 
        self.buff_frames = load_animation_sequence(
            "assets/effects/buffanim",
            size=(1, 2)
        )
        
        self.buff_frame_index = 0
        self.buff_anim_speed = 10
        self.buff_anim_timer = 0
        
        self.buff_item = QGraphicsPixmapItem(self)
        self.buff_item.setZValue(195)
        self.buff_item.setVisible(False)
        
        self.is_buffed = False

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
    
    #     return x, y    

    def shrink_hitbox(self, hx, hy, hw, hh, margin):
        """
        Reduit une hitbox en appliquant une marge sur chaque cote.
        Retourne (hx, hy, hw, hh) reduit de `margin` pixels de chaque cote.
        """
        return hx + margin, hy + margin, hw - 2 * margin, hh - 2 * margin

    def move(self, dx, dy, dt, scene):
        """
        Deplace l'entite en tenant compte des collisions et de la correction de coin.
        Details :
            - Si self.collision est False, le deplacement est applique sans verification.
            - La hitbox est rétrécie de MARGIN pixels sur chaque cote avant chaque test
            de collision, pour tolérer un leger chevauchement visuel avec les murs.
            - Si self.corner_correction est True et que l'axe est bloque, on tente
            un leger decalage perpendiculaire (corner) dans les deux sens pour faire
            glisser l'entite autour des coins au lieu de la bloquer net.
            - Le nudge applique sur Y lors de la correction X est repercute sur new_y
            pour éviter que le bloc Y ne l'écrase immédiatement après.
        """
        new_x = self.x + dx * self.speed * dt
        new_y = self.y + dy * self.speed * dt

        if not self.collision:
            self.x = new_x
            self.y = new_y
            return

        MARGIN = 6          # Reduction de la hitbox en pixels pour les tests de collision
        corner = self.tile_size * 0.3  # Amplitude du decalage de correction de coin

        def passable(x, y):
            """Retourne True si la hitbox retrecie à (x, y) ne chevauche aucun mur."""
            return not scene.is_blocking_rect(*self.shrink_hitbox(*self.get_hitbox(x, y), MARGIN),entity=self)

        # --- Axe X
        if passable(new_x, self.y):
            self.x = new_x
        elif self.corner_correction:
            for nudge in (corner, -corner):
                if passable(new_x, self.y + nudge) and passable(self.x, self.y + nudge):
                    self.x = new_x
                    self.y += nudge
                    new_y += nudge  # repercuter le nudge pour ne pas ecraser la correction en Y
                    break

        # --- Axe Y
        if passable(self.x, new_y):
            self.y = new_y
        elif self.corner_correction:
            for nudge in (corner, -corner):
                if passable(self.x + nudge, new_y) and passable(self.x + nudge, self.y):
                    self.y = new_y
                    self.x += nudge
                    break
    
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
            print(f"[{class_name.upper()} HP] : {self.pv_main}/{self._pv_max}")

        
        # gestion des degats
        # attaques a 0 degats (ex boomerang) ne font pas flash rouge et ne rendent pas invulnerable
        if damage != 0:
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
            
    def apply_white_flash(self):
        """
        Effet visuel de clignotement blanc (invulnérabilité)
        """
        if not self._base_sprites:
            self._base_sprites = self.sprites.copy()
    
        for key in self.sprites:
            original = self._base_sprites[key]
    
            tinted = original.copy()
    
            painter = QPainter(tinted)
    
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(
                tinted.rect(),
                QColor(255, 255, 255, 45)
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
                if self.scene().is_blocking_rect(hx, hy, hw, hh,self):
                    return
                
                #bloquer le deplacement si oob
                if self._is_out_of_bounds(test_x, self.y):
                    return
    
                self.x = test_x
    
            else:
                test_y = self.y + direction
                hx, hy, hw, hh = self.get_hitbox(self.x, test_y)
    
                if self.scene().is_blocking_rect(hx, hy, hw, hh,self):
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
    
            if not self.scene().is_blocking_rect(hx, hy, hw, hh,self) and not self._is_out_of_bounds(test_x, self.y):
                self.x = test_x
    
        else:
            test_y = self.y + direction * rest
            hx, hy, hw, hh = self.get_hitbox(self.x, test_y)
    
            if not self.scene().is_blocking_rect(hx, hy, hw, hh,self) and not self._is_out_of_bounds(self.x,test_y):
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
        
        # --- INVULNERABILITE ---
        if self.is_invulnerable:
            self.invuln_timer += dt
        
            blink_delay = 0.7   # delai avant clignotement blanc
            blink_speed = 0.3 
        
            if self.invuln_timer >= blink_delay:
                if int((self.invuln_timer - blink_delay) / blink_speed) % 2 == 0:
                    self.apply_white_flash()
                else:
                    if self._base_sprites:
                        self.sprites = self._base_sprites.copy()
        
            if self.invuln_timer >= self.invuln_duration:
                self.is_invulnerable = False
                if self._base_sprites:
                    self.sprites = self._base_sprites.copy()
        
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
    
    def update_stun_animation(self, dt):
        if not self.is_stunned:
            self.stun_item.setVisible(False)
            return
    
        self.stun_item.setVisible(True)
    
        self.stun_anim_timer += dt
        if self.stun_anim_timer >= 1 / self.stun_anim_speed:
            self.stun_anim_timer = 0
            self.stun_frame_index = (self.stun_frame_index + 1) % len(self.stun_frames)
    
        self.stun_item.setPixmap(self.stun_frames[self.stun_frame_index])
    
        # offset du a taille du spr d'anim
        offset_y = -self.tile_size + self.tile_size* self.hitbox_offset_y
        offset_x = (self.hitbox_width- self.tile_size + 2*self.tile_size* self.hitbox_offset_x)/2
    
        self.stun_item.setPos(offset_x, offset_y)
        
    def update_buff_animation(self, dt):
        if not self.is_buffed:
            self.buff_item.setVisible(False)
            return
    
        self.buff_item.setVisible(True)
    
        self.buff_anim_timer += dt
        if self.buff_anim_timer >= 1 / self.buff_anim_speed:
            self.buff_anim_timer = 0
            self.buff_frame_index = (self.buff_frame_index + 1) % len(self.buff_frames)
    
        self.buff_item.setPixmap(self.buff_frames[self.buff_frame_index])
    
        # offset du a taille du spr d'anim
        offset_y = -self.tile_size + self.tile_size* self.hitbox_offset_y
        offset_x = (self.hitbox_width- self.tile_size + 2*self.tile_size* self.hitbox_offset_x)/2
    
        self.buff_item.setPos(offset_x, offset_y)


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
        
        
    
        # direction du vecteur perpendiculaire (si n'existe pas, alors nul)
        kbx = getattr(self, "kb_dir_x", 0)
        kby = getattr(self, "kb_dir_y", 0)
        
        self.stun_perp_x = -kby
        self.stun_perp_y = kbx