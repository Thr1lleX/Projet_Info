# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import random
import math

from game.enemies.enemy import Enemy
from game.settings import settings
from game.attacks.lightning import Lightning

class Polasu(Enemy):
    """Ennemi bloquant les attaques de face et attaquant avec des eclairs."""
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = settings.base_speed * 0.2
        self._pv_max = 6
        self.pv_main = self._pv_max
        self.aggro_range = settings.tile_size * 6.5
        self.damage = 0.5
        
        self.loot = [
            ("mana", 0.30),
            ("bombe", 0.25)
        ]
        
        self.death_cry = "snd_death_polasu"
        self.knockback = 1.5

        # --- GESTION DES SPRITES ---
        self.sprites = {
            "down": QPixmap("assets/enemies/polasu/polasu_down.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "up": QPixmap("assets/enemies/polasu/polasu_up.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "left": QPixmap("assets/enemies/polasu/polasu_left.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "right": QPixmap("assets/enemies/polasu/polasu_right.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            )
        }

        # Sprite initial
        self.direction = "down"
        self.setPixmap(self.sprites[self.direction])
        
        # --- GESTION DU BLOCAGE ---
        self.is_blocking = False
        self.block_timer = 0.0
        self.block_duration = 0.25
        
        # --- GESTION DE L'ATTAQUE LIGHTNING ---
        self.is_attacking = False
        self.lightning_step = 0
        self.lightning_timer = 0.0
        self.lightning_sequence = []

    def take_damage(self, scene, damage, source=None):
        """Surcharge pour annuler les degats si l'attaque vient de face."""
        if self.is_invulnerable:
            return

        blocked = False

        # --- LOGIQUE DE BLOCAGE (BOUCLIER) ---
        if source:
            sx, sy = source.get_center()
            ex, ey = self.get_center()
            
            vx = ex - sx
            vy = ey - sy
            
            if abs(vx) > abs(vy):
                if vx > 0 and self.direction == "left":
                    blocked = True
                elif vx < 0 and self.direction == "right":
                    blocked = True
            else:
                if vy > 0 and self.direction == "up":
                    blocked = True
                elif vy < 0 and self.direction == "down":
                    blocked = True

        if blocked:
            self.is_invulnerable = True
            self.invuln_timer = 0
            
            self.is_blocking = True
            self.block_timer = self.block_duration
            scene.sfx_manager.play("snd_block_polasu")
            
            # ce coup precis a ete bloque
            self._coup_bloque_actuel = True
            return

        # si coup vient d'ailleurs on applique degats normaux
        self._coup_bloque_actuel = False
        super().take_damage(scene, damage, source)
        



    def stun(self, duration):
        """Empeche le stun si le coup a ete bloque (le boomerang doit venir de derriere)."""
        if getattr(self, "_coup_bloque_actuel", False):
            self._coup_bloque_actuel = False
            return

        super().stun(duration)


    def update(self, dt, scene):
        """Met a jour la logique de Polasu (blocage, attaque eclair en sequence)."""
        # --- GESTION DU TIMER DE BLOCAGE ---
        if self.is_blocking:
            self.block_timer -= dt
            if self.block_timer <= 0:
                self.is_blocking = False
                
        # --- GESTION DE L'ATTAQUE EN SÉQUENCE ---
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.is_attacking:
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                if self.lightning_step < 8:
                    offset_x, offset_y = self.lightning_sequence[self.lightning_step]
                    
                    lx = self.x + (offset_x * settings.tile_size)
                    ly = self.y + (offset_y * settings.tile_size)
                    
                    lightning = Lightning(self, lx, ly)
                    scene.addItem(lightning)
                    scene.projectiles.append(lightning)
                    scene.sfx_manager.play("snd_lightning")
                    
                    self.lightning_step += 1
                    self.lightning_timer = 0.15
                else:
                    self.is_attacking = False
                    self.attack_cooldown = 0.5

        # --- IMMOBILISATION S'IL ATTAQUE OU BLOQUE  ---
        original_speed = self.speed
        if self.is_blocking or self.is_attacking:
            self.speed = 0

        # update parent pour pathfinder et try_hitplayer etc.
        super().update(dt, scene)

        self.speed = original_speed
        
        
    def start_lightning_attack(self):
        """Initialise et prepare la sequence d'attaque electrique."""
        self.is_attacking = True
        self.lightning_step = 0
        self.lightning_timer = 0.0
        
        # Les 8 directions en tournant dans le sens horaire
        offsets = [
            (0, -1),  # 0: Haut
            (1, -1),  # 1: Haut-Droite
            (1, 0),   # 2: Droite
            (1, 1),   # 3: Bas-Droite
            (0, 1),   # 4: Bas
            (-1, 1),  # 5: Bas-Gauche
            (-1, 0),  # 6: Gauche
            (-1, -1)  # 7: Haut-Gauche
        ]
        
        # index de depart est la ou il regarde
        start_index = 0
        if self.direction == "right": start_index = 2
        elif self.direction == "down": start_index = 4
        elif self.direction == "left": start_index = 6
        
        # rotation pour mettre la direction voulue en premier
        ordered = offsets[start_index:] + offsets[:start_index]
        
        # premier element fixe
        first = ordered[0]
        
        # le reste est random
        others = ordered[1:]
        random.shuffle(others)
        
        self.lightning_sequence = [first] + others
    
    def try_hit_player(self, scene):
        """Verifie la distance pour declencher l'attaque eclair ou infliger des degats au contact."""
        # degats de contact si joueur lui fonce dessus
        super().try_hit_player(scene)
        
        # verification avant de lancer attaque
        if not self.target or self.is_stunned:
            return
            
        if not self.is_attacking and self.attack_cooldown <= 0:
            # Calcul de la distance avec le joueur
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            
            # declenche si le joueur est a 1 case (ou 1.5 en diagonale)
            if dist <= settings.tile_size * 1.5:
                self.start_lightning_attack()
                
