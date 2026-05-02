# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QApplication, QGraphicsTextItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
#from PyQt5.QtWidgets import QGraphicsRectItem, QApplication
from PyQt5.QtGui import QPen, QColor, QFont, QFontDatabase

from game.config import BASE_TILE_SIZE, BASE_SPEED, DEBUG, TILE_SIZE, EXIT_HOLD_TIME, KEYS, SCALE
from game.fonts import get_font0

from game.entity import Entity
from game.enemies.enemy import Enemy
#from game.window import GameWindow
from game.attacks.sword_slash import SwordSlash
from game.attacks.spear import Spear
from game.attacks.test_fireball import Fireball
from game.attacks.boomerang import Boomerang
from game.animspr import load_animation_sequence
import random

class Player(Entity):
    def __init__(self, scale):
        super().__init__(scale)
        
        self.stun_frames = load_animation_sequence(
            "assets/effects/stunanim",
            size=(1, 2)
        )

        self.setZValue(100)

        self.x = 5 * self.tile_size
        self.y = 5 * self.tile_size
        
        # -- STATS --

        self.speed = BASE_SPEED

        self.pv_max = 6
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
        
        self.corner_correction = False
        
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
        
        self._base_sprites = self.sprites.copy()
        

        self.direction = "down"
        self.setPixmap(self.sprites[self.direction])
        
        #sounds effects de cris pour prise de degats
        self.cries = ["snd_playerhit1","snd_playerhit2"]
        self.death_cry = "snd_deathchara"

        # Forcer sortie du jeu
        self.echap = 0
        
        # Layout de exit
        font = get_font0(size=int(0.65 * TILE_SIZE))
        offset_exit = 1 * SCALE
        
        self.exit_label_shadow = QGraphicsTextItem()
        self.exit_label_main = QGraphicsTextItem()
        self.exit_label_shadow = QGraphicsTextItem()
        self.exit_label_shadow.setZValue(2999)
        self.exit_label_main.setZValue(3000)
        
        self.exit_label_shadow.setPos(0.25 * TILE_SIZE + offset_exit,0.25 * TILE_SIZE + offset_exit)
        self.exit_label_main.setPos(0.25 * TILE_SIZE,0.25 * TILE_SIZE)
        
        self.exit_label_added = False 
        self.exit_label_shadow.setFont(font)
        self.exit_label_main.setFont(font)
        self.exit_label_shadow.hide()
        self.exit_label_main.hide()
            
        
        # etats d'attaque
        self.is_attacking = False
        self.is_usingspear = False
        self.current_sword = None
        self.current_spear = None
        self.projectiles = []
        self.projectiles_cooldown = 0
        self.projectiles_delay = 0.4 #0.5s min entre chaque
        
        self.shout_pressed = False

        self.can_go_on_water = True
        
        # update graphics
        self.update_graphics()

    def key_press(self, key):
        self.keys.add(key)

    def key_release(self, key):
        self.keys.discard(key)
 

    def update(self, dt, scene):
        """
        Cette fonction va s'occuper de charger logique au fur et a mesure en gros
        
        On divise ca en 3:
            - les systemes globaux qui doivent toujours etre updates
            - tout ce qui est lie au deplacement
            - follow logic, en l'occurence les armes suivent le joueur lors de knockback
        """
        self.update_damage_state(dt) # invuln, clignot etc.
        self.update_stun_animation(dt)
        
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        if self.projectiles_cooldown > 0:
            self.projectiles_cooldown = max(0, self.projectiles_cooldown - dt)
        
        # mise a jours des projectiles en fond
        for proj in self.projectiles[:]:
            proj.update(dt, scene)
            if proj.scene() is None:
                self.projectiles.remove(proj)

        if scene.is_transitioning:
            return

        # # 2 - deplacements
        # bloque le joueur si knockback, mais autorise wiggle de stun
        if self.kb_active:
            self.apply_knockback(dt, scene)
        if self.is_stunned:
            self.apply_stun_wiggle(dt, scene)
        elif self.is_attacking or self.is_usingspear:
            # bloque le joeur durant animation d'attaque
            pass
        else:
            self.handle_inputs(dt, scene)
            
        # mise a jour des armes ! necessairement apres mouvement!
        self.update_held_weapons(dt, scene)
        self.handle_exit_logic(dt, scene)
        self.update_graphics()
        self.update_stun_animation(dt)
        
        
        # --- SPGHETTI CODE!!!!! ---
        if getattr(self, 'is_stunned', False) and hasattr(self, 'stun_item') and self.stun_item:
            self.stun_item.setVisible(True)
            self.stun_item.setOpacity(1.0)
            
            from PyQt5.QtWidgets import QGraphicsItem
            self.stun_item.setFlag(QGraphicsItem.ItemIgnoresParentOpacity, True)
            
            self.stun_item.setZValue(200)
            
            if self.stun_item.scene() is None:
                scene.addItem(self.stun_item)

            self.stun_item.setPos(self.x, self.y-self.tile_size)
        # --- FIN DU HACK ---

    def update_held_weapons(self, dt, scene):
        """
        mise a jour de position et animation des armes bound au joueur
        """
        if self.is_attacking and self.current_sword:
            self.current_sword.update(dt, scene)
            
        if self.is_usingspear and self.current_spear:
            self.current_spear.update(dt, scene)

    def handle_inputs(self, dt, scene):
        """
        Gestion des touches
        """
        dx, dy = 0, 0
        if not self.kb_active:
            if KEYS["UP"] in self.keys:    dy -= 1; self.direction = "up"
            if KEYS["DOWN"] in self.keys:  dy += 1; self.direction = "down"
            if KEYS["LEFT"] in self.keys:  dx -= 1; self.direction = "left"
            if KEYS["RIGHT"] in self.keys: dx += 1; self.direction = "right"

         # normalisation diagonale
        if dx != 0 and dy != 0:
            dx *= 0.707106
            dy *= 0.707106

        self.move(dx, dy, dt, scene)

        if KEYS["ATTACK"] in self.keys:
            if not self.attack_pressed and self.attack_cooldown == 0:
                self.attack(scene)
                self.attack_pressed = True
                self.attack_cooldown = self.attack_delay
        elif KEYS["ITEM"] in self.keys:
            if not self.attack_pressed and self.projectiles_cooldown == 0:
                self.throw_boomerang(scene)
                self.attack_pressed = True
                self.projectiles_cooldown = self.projectiles_delay
        else:
            self.attack_pressed = False
        
        if DEBUG:
            if KEYS["CROUCH"] in self.keys:
                self.speed = BASE_SPEED * 0.5
            elif KEYS["SPRINT"] in self.keys:
                self.speed = BASE_SPEED * 5
            else:
                self.speed = BASE_SPEED

    
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

    # def take_damage(self, scene, damage, source=None):
    #     scene.sfx_manager.play("snd_deathchara")
    #     self.stun(20)
    #     super().take_damage(scene, damage, source)


    def die(self):
        scene = self.scene()
        if scene:
            sm = getattr(scene, 'screen_manager', None)
            if sm is not None:
                sm.on_game_over()
            else:
                scene.game_over()   # retro-compatibilite si pas de ScreenManager

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
                self.exit_label_main.hide()
                self.exit_label_shadow.hide()
            self.echap = 0
            return

        # -- gestion de la sortie (echap)---
        if not self.exit_label_added:
            scene.addItem(self.exit_label_main)
            scene.addItem(self.exit_label_shadow)
            self.exit_label_added = True

        self.echap += dt
        self.exit_label_main.show()
        self.exit_label_shadow.show()
        
        if DEBUG:
            print(f"Échap maintenu : {self.echap:.2f}s / {EXIT_HOLD_TIME}s") 

        # calcul de progression pour affichage
        progress = min(self.echap / EXIT_HOLD_TIME, 1.0)
        
        alpha = int(progress * 255)
        self.exit_label_main.setDefaultTextColor(QColor(255, 255, 255, alpha))
        self.exit_label_shadow.setDefaultTextColor(QColor(23, 33, 136, alpha))

        # points de sus tous les 0.25 EXIT_HOLD_TIME
        dots = "." * int(progress / 0.25) 
        text = f"EXIT{dots}"
        self.exit_label_main.setPlainText(text)
        self.exit_label_shadow.setPlainText(text)
        
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

    def stop_movement(self):
        """
        vide les touches actives pour eviter mvts faantomes 
        """
        self.keys.clear()
        self.attack_pressed = False
        
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

    def is_projectile_active(self, projectile_class):
        for p in self.projectiles:
            if isinstance(p, projectile_class) and getattr(p, 'only_one', False):
                return True
        return False
        
    def shoot_fireball(self, scene):
        new_fireball = Fireball(self, self.direction)
        scene.addItem(new_fireball)
        self.projectiles.append(new_fireball)
        
        
    def throw_boomerang(self, scene):

        if self.is_projectile_active(Boomerang):
            if DEBUG:
                print("Ne peut pas lancer plus d'un boomerang à la fois")
            return 
        scene.sfx_manager.play("snd_throw")
            
        new_boom = Boomerang(self, self.direction)
        self.projectiles.append(new_boom)
        scene.addItem(new_boom)
    
    