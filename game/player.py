# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QApplication, QGraphicsTextItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
#from PyQt5.QtWidgets import QGraphicsRectItem, QApplication
from PyQt5.QtGui import QPen, QColor, QFont, QFontDatabase

from game.config import BASE_TILE_SIZE, BASE_SPEED, DEBUG, TILE_SIZE
from game.config import KEYS, EXIT_HOLD_TIME

from game.entity import Entity
from game.enemies.enemy import Enemy
from game.fonts import get_font0
#from game.window import GameWindow
from game.attacks.sword_slash import SwordSlash
from game.attacks.spear import Spear
import random

class Player(Entity):
    def __init__(self, scale):
        super().__init__(scale)

        self.setZValue(100)

        self.x = 5 * self.tile_size
        self.y = 5 * self.tile_size
        
        # -- STATS --

        self.speed = BASE_SPEED

        self.pv_max = 5
        self.pv_main = self.pv_max
        
        # --Attaques--
        
        self.attack_cooldown = 0
        self.attack_delay = 0.2   # s entre attaques, doit etre supp a anim
        self.attack_pressed = False

        self.damage = 1 # degats qu'inflinge le joueur
        
        # -- Dammaged--
        self.invuln_duration = 0.60 #en s
        
        # --- HITBOX ---
        self.hitbox_offset_x = 2/BASE_TILE_SIZE
        self.hitbox_offset_y = 1/BASE_TILE_SIZE

        self.hitbox_width = self.tile_size * (1-4/BASE_TILE_SIZE)
        self.hitbox_height = self.tile_size * (1-1/BASE_TILE_SIZE)
        
        self.collision = 1

        # DEBUG couleur
        if DEBUG:
            self.debug_rect.setPen(QPen(QColor("green"), 1))


        self.keys = set()
        # --- SPRITES ---
        self.sprites = {
            "down": QPixmap("assets/chara_face.png").scaled(
                self.tile_size, self.tile_size, transformMode=Qt.FastTransformation
            ),
            "up": QPixmap("assets/chara_back.png").scaled(
                self.tile_size, self.tile_size, transformMode=Qt.FastTransformation
            ),
            "left": QPixmap("assets/chara_left.png").scaled(
                self.tile_size, self.tile_size, transformMode=Qt.FastTransformation
            ),
            "right": QPixmap("assets/chara_right.png").scaled(
                self.tile_size, self.tile_size, transformMode=Qt.FastTransformation
            ),
        }
        

        self.direction = "down"
        self.setPixmap(self.sprites[self.direction])
        
        #sounds effects de cris pour prise de degats
        self.cries = ["snd_playerhit1","snd_playerhit2"]
        self.death_cry = "snd_deathchara"

        # Quitter le jeu
        self.echap = 0
        
        # Layout de exit
        self.exit_label = QGraphicsTextItem()
        self.exit_label.setZValue(3000)
        self.exit_label.setPos(0.25 * TILE_SIZE, 0.25 * TILE_SIZE)
        
        font = get_font0(size=int(0.65 * TILE_SIZE))
        self.exit_label.setFont(font)
        self.exit_label.hide()
        self.exit_label_added = False
        self.is_attacking = False
        self.is_usingspear = False
        self.current_sword = None
        self.current_spear = None
        
        self.shout_pressed = False
        
        # update graphics
        self.update_graphics()

    def key_press(self, key):
        self.keys.add(key)

    def key_release(self, key):
        self.keys.discard(key)
 
    
    def update(self, dt, scene):
        """
        Fonction qui s'occupe de reagir aux touches
        On utilise update_graphics de entity.py
        donc ici, simplement pour touches
        """

        self.handle_exit_logic(dt, scene)
        
        # priorite au knockback pour bloquer mvt du joueur
        if self.kb_active:
            self.apply_knockback(dt, scene)
            
            # update des attaques pendant knockback
            if self.is_attacking and self.current_sword:
                self.current_sword.update(dt, scene)
            # plus tard remplacer par item au lieu de lance
            if self.is_usingspear and self.current_spear:
                self.current_spear.update(dt, scene)
        
            self.update_graphics()
            self.update_damage_state(dt)
            return

        # # priorite au knockback pour bloquer mvt du joueur
        # if self.kb_active:
        #     self.apply_knockback(dt, scene)
            
        #     # il faut aussi updater animation de epee durant knockback si attaque
        #     if self.is_attacking and self.current_sword:
        #         self.current_sword.update(dt,scene)
        #     self.update_graphics()
        #     self.update_damage_state(dt)
        #     return
        # # plus tard remplacer par item au lieu de lance
        #     if self.is_usingspear and self.current_spear:
        #         self.current_spear.update(dt,scene)
        #     self.update_graphics()
        #     self.update_damage_state(dt)
        #     return
        # prio au stun ensuite, mais autorise wiggle (voir entity.py)
        if self.is_stunned:
            self.apply_stun_wiggle(dt,scene)
            self.update_graphics()
            self.update_damage_state(dt)
            return
            
        if not scene.is_transitioning:
            pass
        
        # bloque le joeur durant animation d'attaque
        if self.is_attacking:
            if self.current_sword:
                self.current_sword.update(dt, scene)
    
            self.update_graphics()
            self.update_damage_state(dt)
            return
        
        
        if self.is_usingspear:
            if self.current_spear:
                self.current_spear.update(dt, scene)
    
            self.update_graphics()
            self.update_damage_state(dt)
            return

        # --COOLDOWN ATTAQUE ---
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
            if self.attack_cooldown < 0:
                self.attack_cooldown = 0
        
        # -- MOUVEMENTS--
        dx, dy = 0, 0
    
        if KEYS["UP"] in self.keys:
            dy -= 1
            self.direction = "up"
        if KEYS["DOWN"] in self.keys:
            dy += 1
            self.direction = "down"
        if KEYS["LEFT"] in self.keys:
            dx -= 1
            self.direction = "left"
        if KEYS["RIGHT"] in self.keys:
            dx += 1
            self.direction = "right"
        
        if KEYS["SHOUTS"] in self.keys:
            if not self.shout_pressed:
                self.shout(scene)
                self.shout_pressed = True
        else:
            self.shout_pressed = False
            
        if KEYS["ATTACK"] in self.keys:
            if not self.attack_pressed and self.attack_cooldown == 0:
                self.attack(scene)
                self.attack_pressed = True
                self.attack_cooldown = self.attack_delay
        else:
            self.attack_pressed = False     
        
        if KEYS["ITEM"] in self.keys:
            if not self.attack_pressed and self.attack_cooldown == 0:
                self.spear(scene)
                self.attack_pressed = True
                self.attack_cooldown = self.attack_delay
        else:
            self.attack_pressed = False
            
        if DEBUG:
            if KEYS["CROUCH"] in self.keys:
                self.speed = BASE_SPEED * 0.5
            elif KEYS["SPRINT"] in self.keys:
                self.speed = BASE_SPEED * 5
            else:
                self.speed = BASE_SPEED
                
        # normalisation diagonale
        if dx != 0 and dy != 0:
            dx *= (2**0.5)/2
            dy *= (2**0.5)/2
    
        if self.is_attacking and self.current_sword:
            self.current_sword.update(dt, scene)
            
        self.move(dx, dy, dt, scene)
        self.update_graphics()
        self.update_damage_state(dt)
    
    def get_hitbox(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y
    
        return (
            x + self.hitbox_offset_x*self.tile_size,
            y + self.hitbox_offset_y*self.tile_size,
            self.hitbox_width,
            self.hitbox_height
        )


    def die(self):
        scene = self.scene()
        if scene:
            scene.game_over()

    """
    Fonctions pour quitter le jeu
    """
    
    def handle_exit_logic(self, dt, scene):
        """
        gere maintien de l'echap et affichage du texte EXIT
        utilise dans update
        """

        # -- gestion de la sortie (echap)---
        if KEYS["LEAVE"] not in self.keys:
            if self.echap > 0:
                self.exit_label.hide()
            self.echap = 0
            return

        # -- gestion de la sortie (echap)---
        if not self.exit_label_added:
            scene.addItem(self.exit_label)
            self.exit_label_added = True

        self.echap += dt
        self.exit_label.show()

        if DEBUG:
            print(f"Échap maintenu : {self.echap:.2f}s / {EXIT_HOLD_TIME}s") 

        # calcul de progression pour affichage
        progress = min(self.echap / EXIT_HOLD_TIME, 1.0)
        
        alpha = int(progress * 255)
        self.exit_label.setDefaultTextColor(QColor(255, 255, 255, alpha))

        # points de sus tous les 0.25 EXIT_HOLD_TIME
        dots = "." * int(progress / 0.25) 
        self.exit_label.setPlainText(f"EXIT{dots}")

        # delai atteint
        if self.echap >= EXIT_HOLD_TIME:
            # on bloque le compteur pour ne pas qu'il continue apres (securite)
            self.echap = -999999 
            # declenche fermeture
            self.trigger_quit(scene)

    def trigger_quit(self, scene):
        """
        trigger de fermeture de fenetre
        """
        # on arrête le Timer de la scene
        if hasattr(scene, 'timer'):
            scene.timer.stop()
            
        views = scene.views()
        if views:
            window = views[0].window()
            # ferme fenetre
            if hasattr(window, 'quitter_jeu'):
                window.quitter_jeu()
            else:
                window.close()
    
    ##### ATTAQUES ####

    # def attack(self, scene):
    #     for item in scene.items():    
    #         if isinstance(item, Enemy):
    #             item.take_damage(self.damage, self)
    #             item.stun(0, wiggle=True)

    def attack(self, scene):
        if self.is_attacking:
            return # Empêche de spammer l'attaque
            
        self.is_attacking = True
        
        # le 1er son de voix est joue plus souvent
        if random.random() < 0.66:
            voice = "snd_charavoice1"
        else: 
            voice = "snd_charavoice2"
        scene.sfx_manager.play(voice)
        
        # Créer l'épée et l'ajouter à la scène
        self.current_sword = SwordSlash(self, self.direction)
        scene.addItem(self.current_sword)
    
    def shout(self, scene):
        """
        Fonction juste pour tester les sfx
        """
        if DEBUG:
            print("[PLAYER] Shout!")
        scene.sfx_manager.play("snd_sad")
    
    def spear(self, scene):
        if self.is_attacking:
            return # Empêche de spammer l'attaque
            
        self.is_usingspear = True
        
        # # le 1er son de voix est joue plus souvent
        # if random.random() < 0.66:
        #     voice = "snd_charavoice1"
        # else: 
        #     voice = "snd_charavoice2"
        # scene.sfx_manager.play(voice)
        
        # Créer l'épée et l'ajouter à la scène
        self.current_spear = Spear(self, self.direction)
        scene.addItem(self.current_spear)
    
    