# -*- coding: utf-8 -*-

import random
import math
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPixmap

from game.enemies.enemy import Enemy
from game.settings import settings
from game.animspr import load_animation_sequence

# Adapte le chemin selon ton architecture
from game.attacks.shock_wave import ShockWave 

class BrasDroit(Enemy):
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS DE BASE ---
        self._pv_max = 60
        self.pv_main = self._pv_max
        self.damage = 1
        self.give_stun = 0.5
        self.knockback = 2.0
        self.duree_knockback = 0.25
        
        self.effect_immunity_duration = 5
        
        # Tailles (2x2 tiles)
        self.hitbox_width = settings.tile_size * 2
        self.hitbox_height = settings.tile_size * 2
        
        self.use_pathfinding = False
        self.aggro_range = settings.tile_size * 20
        
        # --- SPRITES ET ANIMATIONS ---
        self.frames = load_animation_sequence("assets/enemies/bras_droit/right_arm", (2, 2), 2)
        self.current_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.25 
        
        self.setPixmap(self.frames[0])

        # --- GESTION DES ETATS ---
        self.state = "chasing" 
        self.shockwave_timer = random.uniform(5.0, 10.0)
        self.action_timer = 0.0 
        
        self.current_attack = None
        self.is_attacking = False

        # Timer indépendant dédié au clignotement visuel continu
        self.blink_timer = 0.0
        
        # --- AUDIO ---
        self.spawn_sound_played = False
        self.sfx_timer = random.uniform(3.0, 7.0)

    def update_graphics(self):
        """ 
        Surcharge cruciale. C'est ici qu'on force l'application des filtres
        à CHAQUE frame de calcul du jeu pour une réactivité instantanée.
        """
        self.setPos(self.x, self.y)
        
        # Sécurité : On rafraîchit le pixmap de la frame courante à chaque frame
        if hasattr(self, 'frames') and self.frames:
            self.setPixmap(self.frames[self.current_frame])

    def update(self, dt, scene):
        # Progression du timer de clignotement
        self.blink_timer += dt

        # 1. Audio
        if not self.spawn_sound_played:
            scene.sfx_manager.play("snd_bras_droit")
            self.spawn_sound_played = True
            
        self.sfx_timer -= dt
        if self.sfx_timer <= 0:
            sfxs = ["snd_traverse","snd_fromage","snd_savon"]
            scene.sfx_manager.play(random.choice(sfxs))
            self.sfx_timer = random.uniform(5.0, 11.0) 

        # 2. Logique pure de l'animation (on ne change QUE l'index de la frame)
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.current_frame = (self.current_frame + 1) % len(self.frames)

        # 3. Machine à états
        if self.state == "chasing":
            self.speed = settings.base_speed * 0.4
            self.is_invulnerable = False
            
            if self.shockwave_timer > 0:
                self.shockwave_timer -= dt
            
            if self.shockwave_timer <= 0:
                player = self.target if self.target else (scene.player if hasattr(scene, 'player') else None)
                
                if player:
                    c1 = self.get_center()
                    c2 = player.get_center()
                    
                    cx1 = c1.x() if hasattr(c1, 'x') else c1[0]
                    cy1 = c1.y() if hasattr(c1, 'y') else c1[1]
                    cx2 = c2.x() if hasattr(c2, 'x') else c2[0]
                    cy2 = c2.y() if hasattr(c2, 'y') else c2[1]
                    
                    dist = math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                    
                    if dist < 2.5 * settings.tile_size:
                        self.state = "attacking"
                        self.action_timer = 3.0 
                        self.is_attacking = True
                        
                        self.current_attack = ShockWave(self, self.direction)
                        self.current_attack.setPos(self.x, self.y)
                        scene.addItem(self.current_attack)
                        scene.sfx_manager.play("snd_charge_bras")

        elif self.state == "attacking":
            self.speed = 0 
            self.is_invulnerable = True
            self.kb_active = False 
            self.is_stunned = False 
            
            if self.current_attack:
                self.current_attack.update(dt, scene)
            
            self.action_timer -= dt
            if self.action_timer <= 0:
                self.state = "recovering"
                self.action_timer = 2.5 
                self.is_invulnerable = False 
                self.is_attacking = False
                self.current_attack = None

        elif self.state == "recovering":
            self.speed = 0 
            self.action_timer -= dt
            if self.action_timer <= 0:
                self.state = "chasing"
                self.shockwave_timer = random.uniform(5.0, 10.0) 

        self.update_damage_state(dt)
        super().update(dt, scene) # super().update() appellera automatiquement update_graphics()

    def die(self):
        if self.current_attack:
            if hasattr(self.current_attack, 'die'):
                self.current_attack.die()
            self.current_attack = None
            self.is_attacking = False
            
        scene = self.scene()
        scene.sfx_manager.stop_all_except(self.death_cry)
        if scene:
            if hasattr(scene, "music_manager"):
                scene.music_manager.stop()
            scene.sfx_manager.play("snd_finito")
            
        super().die()

    def setPixmap(self, pixmap):
        """ Applique dynamiquement les teintes à chaque exécution sur le sprite animé """
        if not pixmap or pixmap.isNull():
            super().setPixmap(pixmap)
            return

        # 1. PRIORITÉ ABSOLUE : Flash rouge lors des dégâts reçus (is_damaged)
        if getattr(self, "is_damaged", False):
            tinted = pixmap.copy()
            painter = QPainter(tinted)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(tinted.rect(), QColor(255, 0, 0, 140)) # Rouge à 140 d'opacité
            painter.end()
            super().setPixmap(tinted)
            return

        # 2. SECONDE PRIORITÉ : Clignotement blanc (Invulnérabilité aux dégâts OU état "attacking")
        if getattr(self, "is_invulnerable", False):
            # On utilise le blink_timer global à haute fréquence pour une alternance propre
            if int(self.blink_timer * 15) % 2 == 0:
                tinted = pixmap.copy()
                painter = QPainter(tinted)
                painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
                painter.fillRect(tinted.rect(), QColor(255, 255, 255, 160)) # Blanc à 160 d'opacité pour bien le voir
                painter.end()
                super().setPixmap(tinted)
                return

        # 3. Rendu normal sans effet actif
        super().setPixmap(pixmap)