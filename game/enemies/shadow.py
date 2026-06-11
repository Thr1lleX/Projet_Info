# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import math
import random

from game.enemies.enemy import Enemy
from game.settings import settings
from game.attacks.sword_shadow import SwordShadow

# Import des classes d'épée autorisées à blesser Shadow
from game.attacks.sword_slash import SwordSlash
from game.attacks.sword_slash_upgrade import SwordSlashUpgrade
from game.attacks.sword_slash_tungsten import SwordSlashTungsten

class Shadow(Enemy):
    """Ennemi copiant les mouvements et attaques du joueur (effet miroir)."""
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS DE BASE ---
        # On initialise avec la vitesse de base pour que le moteur de collisions physique fonctionne
        self.speed = settings.base_speed 
        self._pv_max = 6
        self.pv_main = self._pv_max
        self.damage = 2
        
        # États d'action
        self.is_effect_immune = True  # Immunité totale au stun dès le départ
        self.is_attacking = False     # Géré par SwordShadow lors du cycle de vie de l'attaque
        self.current_attack = None

        # Timer pour l'attaque automatique si le joueur reste devant (1.5s)
        self.player_in_front_timer = 0.0

        # --- GESTION DES SPRITES ---
        self.sprites = {
            "down": QPixmap("assets/enemies/shadow/shadow_face.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "up": QPixmap("assets/enemies/shadow/shadow_back.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "left": QPixmap("assets/enemies/shadow/shadow_left.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "right": QPixmap("assets/enemies/shadow/shadow_right.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            )
        }

        self.direction = "down"
        self.setPixmap(self.sprites[self.direction])
        
        
        self.cries = ["snd_playerhit1","snd_playerhit2"]
        self.death_cry = "snd_shadow_death"
        
        # timer pour attaque automatique si le joueur reste devant
        self.player_in_front_timer = 0.0
        self.is_charging_proximity_attack = False
        self.can_go_on_water = True
        

    def stun(self, duration, wiggle=True):
        """Immunise au stun."""
        return

    def take_damage(self, scene, damage, source=None):
        """Ne peut etre touche que par une epee."""
        if not source or not isinstance(source, (SwordSlash, SwordSlashUpgrade, SwordSlashTungsten)):
            return
        super().take_damage(scene, damage, source)

    def trigger_mirror_attack(self, scene):
        if not self.target or self.is_attacking:
            return
            
        self.is_attacking = True
        copied_damage = self.damage
        
        # On cherche l'arme active du joueur dans la scene pour copier ses degats
        for item in scene.items():
            if isinstance(item, (SwordSlash, SwordSlashUpgrade, SwordSlashTungsten)) and item.source == self.target:
                copied_damage = item.damage
                break

        self.current_attack = SwordShadow(self, self.direction, damage=copied_damage)
        self.current_attack.setPos(self.x, self.y)
        scene.addItem(self.current_attack)
        if random.random() < 0.66:
            voice = "snd_charavoice2"
        else: 
            voice = "snd_charavoice1"
        scene.sfx_manager.play(voice)

    def update(self, dt, scene):
        if not self.target:
            if self.is_invulnerable:
                self.invuln_timer += dt
                if self.invuln_timer >= self.damage_duration:
                    self.is_invulnerable = False
            return

        # --- GESTION DES TIMERS ET ETATS ANCESTRAUX ---
        if self.is_invulnerable:
            self.invuln_timer += dt
            if self.invuln_timer >= self.damage_duration:
                self.is_invulnerable = False
                
        self.update_graphics()
        self.update_damage_state(dt)

        # --- MOUVEMENT EN MIROIR PARFAIT (Controles purs) ---
        if not self.is_charging_proximity_attack and not self.is_attacking:
            self.speed = self.target.speed 
    
            # On extrait les intentions de déplacement directes du joueur via ses touches (ignore le knockback)
            p_dx = 0
            p_dy = 0
            if settings.keys["UP"] in self.target.keys:    p_dy -= 1
            if settings.keys["DOWN"] in self.target.keys:  p_dy += 1
            if settings.keys["LEFT"] in self.target.keys:  p_dx -= 1
            if settings.keys["RIGHT"] in self.target.keys: p_dx += 1
    
            if p_dx != 0 and p_dy != 0:
                p_dx *= 0.707106
                p_dy *= 0.707106
    
            # Application de l'inversion absolue (effet miroir)
            mirror_dx = -p_dx
            mirror_dy = -p_dy
    
            if mirror_dx != 0 or mirror_dy != 0:
                # Orientation graphique de Shadow selon son vecteur opposé
                if abs(mirror_dx) > abs(mirror_dy):
                    self.direction = "right" if mirror_dx > 0 else "left"
                else:
                    self.direction = "down" if mirror_dy > 0 else "up"
                    
                self.setPixmap(self.sprites[self.direction])
                
                # Deplacement physique securise via le moteur de collisions
                self.move(mirror_dx, mirror_dy, dt, scene)

        # --- COPIE DE L'ATTAQUE DE L'EPEE ---
        player_is_attacking = False
        for item in scene.items():
            if isinstance(item, (SwordSlash, SwordSlashUpgrade, SwordSlashTungsten)) and item.source == self.target:
                # Déclenchement uniquement au tout début de l'animation de l'épée du joueur
                if hasattr(item, 'current_frame') and item.current_frame <= 1:
                    player_is_attacking = True
                break

        if player_is_attacking:
            self.trigger_mirror_attack(scene)

        # --- MISE A JOUR DE LA POSITION DE L'EPEE DE SHADOW ---
        if self.is_attacking and self.current_attack:
            self.current_attack.update(dt, scene)

        # --- LOGIQUE DE PROXIMITÉ "JOUEUR DEVANT PENDANT 1.5s" ---
        player_in_front = False
        
        tx, ty = self.target.x / settings.tile_size, self.target.y / settings.tile_size
        sx, sy = self.x / settings.tile_size, self.y / settings.tile_size

        if self.direction == "down" and abs(tx - sx) < 0.8 and 0.5 <= (ty - sy) <= 1.5:
            player_in_front = True
        elif self.direction == "up" and abs(tx - sx) < 0.8 and 0.5 <= (sy - ty) <= 1.5:
            player_in_front = True
        elif self.direction == "right" and abs(ty - sy) < 0.8 and 0.5 <= (tx - sx) <= 1.5:
            player_in_front = True
        elif self.direction == "left" and abs(ty - sy) < 0.8 and 0.5 <= (sx - tx) <= 1.5:
            player_in_front = True
        
        # Gestion du timer et de la charge
        if not self.is_charging_proximity_attack:
            # Si Shadow ne charge pas encore, il faut que le joueur soit devant
            if player_in_front:
                self.player_in_front_timer += dt
                if self.player_in_front_timer >= 0.75:
                    # Le seuil est atteint : Shadow s'engage dans son attaque !
                    self.is_charging_proximity_attack = True
                    scene.sfx_manager.play("snd_shadow_charge")
            else:
                # Le joueur s'est échappé à temps, on réinitialise
                self.player_in_front_timer = 0.0
        else:
            # Shadow est en train de charger : le timer continue de tourner QUOI QU'IL ARRIVE
            self.player_in_front_timer += dt
            
            # A 1.5s (1.1s d'attente + 0.4s de charge), le coup part
            if self.player_in_front_timer >= 1.5:
                self.trigger_mirror_attack(scene)
                # Reset complet après l'attaque
                self.player_in_front_timer = 0.0
                self.is_charging_proximity_attack = False

        # Desactivation des dégâts de contact passifs (facultatif)
        self.try_hit_player(scene)

    def try_hit_player(self, scene):
        """Surcharge pour empecher les degats de collision simples."""
        pass

    def die(self):
        # Si une epee est active au moment de la mort, on la detruit
        if self.current_attack:
            if hasattr(self.current_attack, 'die'):
                self.current_attack.die()
            
            self.current_attack = None
            self.is_attacking = False
        super().die()