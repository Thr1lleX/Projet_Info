# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QApplication, QGraphicsTextItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
#from PyQt5.QtWidgets import QGraphicsRectItem, QApplication
from PyQt5.QtGui import QPen, QColor, QFont, QFontDatabase

from game.config import BASE_TILE_SIZE, DEBUG, EXIT_HOLD_TIME, DUREE_BUFF
from game.fonts import get_font0

from game.entity import Entity
from game.enemies.enemy import Enemy
#from game.window import GameWindow
from game.attacks.sword_slash import SwordSlash
from game.attacks.sword_slash_upgrade import SwordSlashUpgrade
from game.item_effects import use_item
from game.attacks.spear import Spear
from game.attacks.test_fireball import Fireball
from game.attacks.boomerang import Boomerang
from game.animspr import load_animation_sequence
import random
from game.settings import settings

class Player(Entity):
    def __init__(self, scale):
        super().__init__(scale)
        
        self.stun_frames = load_animation_sequence(
            "assets/effects/stunanim",
            size=(1, 2)
        )

        self.setZValue(100)

        self.x = 0
        self.y = 0

        # -- STATS --

        self.speed = settings.base_speed

        self._pv_max = 6
        self.pv_main = self._pv_max
        
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

        self.hitbox_width = settings.tile_size * (1-4/BASE_TILE_SIZE)
        self.hitbox_height = settings.tile_size * (1-1/BASE_TILE_SIZE) 
        
        self.corner_correction = False
        
        self.collision = 1

        # --- buffs ---
        
        self._buff_timer = 0.0
        self._base_damage = 1
        self._base_speed = settings.base_speed
        self.buff_speed_multiplier = 1.0
        self.debug_speed_multiplier = 1.0
        
        # DEBUG couleur
        if DEBUG:
            self.debug_rect.setPen(QPen(QColor("green"), 1))


        self.keys = set()
        # --- SPRITES ---
        self.sprites = {
            "down": QPixmap("assets/chara_face.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "up": QPixmap("assets/chara_back.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "left": QPixmap("assets/chara_left.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
            ),
            "right": QPixmap("assets/chara_right.png").scaled(
                settings.tile_size, settings.tile_size, transformMode=Qt.FastTransformation
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
        font = get_font0(size=int(10))
        offset_exit = 1 * settings.scale
        
        self.exit_label_shadow = QGraphicsTextItem()
        self.exit_label_main = QGraphicsTextItem()
        self.exit_label_shadow = QGraphicsTextItem()
        self.exit_label_shadow.setZValue(2999)
        self.exit_label_main.setZValue(3000)
        
        self.exit_label_shadow.setPos(0.25 * settings.tile_size + offset_exit,0.25 * settings.tile_size + offset_exit)
        self.exit_label_main.setPos(0.25 * settings.tile_size,0.25 * settings.tile_size)
        
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
        self.shout_cooldown = 0
        self.shout_delay = 1.0
        
        # INTERACTION
        self.interact_pressed = False
        if DEBUG:
            self.interact_debug_rect = QGraphicsRectItem()
            self.interact_debug_rect.setPen(QPen(QColor("yellow"), 2))
            self.interact_debug_rect.setZValue(9999)
            self.interact_debug_rect.hide()
        
        # update graphics
        self.update_graphics()

    def key_press(self, key):
        self.keys.add(key)
        
        scene = self.scene()
        if scene is None:
            return
            
        # gestion exclusive de l'interaction
        if key == settings.keys["INTERACT"]:
            if scene.dialogue_manager.active:
                scene.dialogue_manager.advance()
            else:
                self.try_interact(scene)

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
        # ---
        self.get_flags_state(scene)
        # ---
        self.update_damage_state(dt) # invuln, clignot etc.
        self.update_stun_animation(dt)
        self.update_buff_animation(dt)
        
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        # buff potion expiration
        if self._buff_timer > 0:
            self._buff_timer -= dt
            self.is_buffed = True
            if self._buff_timer <= 0:
                self._buff_timer = 0
                self.damage = self._base_damage
                self.buff_speed_multiplier = 1.0    
                self.is_buffed = False                            
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
        
        if self.shout_cooldown > 0:
            self.shout_cooldown = max(0, self.shout_cooldown - dt)
            
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

            self.stun_item.setPos(self.x, self.y-settings.tile_size)
        # --- FIN DU HACK ---
        
        # --- SPAGHETTI CODE BUFF!!!!! ---
        if getattr(self, 'is_buffed', False) and hasattr(self, 'buff_item') and self.buff_item:
            self.buff_item.setVisible(True)
            self.buff_item.setOpacity(1.0)
        
            from PyQt5.QtWidgets import QGraphicsItem
            self.buff_item.setFlag(QGraphicsItem.ItemIgnoresParentOpacity, True)
        
            self.buff_item.setZValue(200)
        
            if self.buff_item.scene() is None:
                scene.addItem(self.buff_item)
        
            self.buff_item.setPos(self.x, self.y - settings.tile_size)
        # --- FIN DU HACK BUFF ---

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
        
        #bloque mouvements du joueur si dialogue
        if scene.dialogue_manager.active:
            self.attack_pressed = True
            return
        
        dx, dy = 0, 0
        if not self.kb_active:
            if settings.keys["UP"] in self.keys:    dy -= 1; self.direction = "up"
            if settings.keys["DOWN"] in self.keys:  dy += 1; self.direction = "down"
            if settings.keys["LEFT"] in self.keys:  dx -= 1; self.direction = "left"
            if settings.keys["RIGHT"] in self.keys: dx += 1; self.direction = "right"

         # normalisation diagonale
        if dx != 0 and dy != 0:
            dx *= 0.707106
            dy *= 0.707106

        self.move(dx, dy, dt, scene)

        if settings.keys["ATTACK"] in self.keys:
            if not self.attack_pressed and self.attack_cooldown == 0:
                self.attack(scene)
                self.attack_pressed = True
                self.attack_cooldown = self.attack_delay
        elif settings.keys["ITEM"] in self.keys:
            if not self.attack_pressed and self.projectiles_cooldown == 0:
                if use_item(self, scene):
                    self.attack_pressed = True
                    self.projectiles_cooldown = self.projectiles_delay
                else:
                    self.attack_pressed = False
        else:
            self.attack_pressed = False
            
        if settings.keys["SHOUTS"] in self.keys:
            if not self.shout_pressed and self.shout_cooldown == 0:
                self.shout(scene)
                self.shout_pressed = True
                self.shout_cooldown = self.shout_delay
        else:
            self.shout_pressed = False
        
        
        if DEBUG:
            if settings.keys["CROUCH"] in self.keys:
                self.debug_speed_multiplier = 0.5
            elif settings.keys["SPRINT"] in self.keys:
                self.debug_speed_multiplier = 5.0
            else:
                self.debug_speed_multiplier = 1.0
            self.update_speed()

    
    def get_hitbox(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y
    
        return (
            x + self.hitbox_offset_x*settings.tile_size,
            y + self.hitbox_offset_y*settings.tile_size,
            self.hitbox_width,
            self.hitbox_height
        )

    def die(self):
        scene = self.scene()
        if scene:
            sm = getattr(scene, 'screen_manager', None)
            if sm is not None:
                sm.on_game_over()
            else:
                scene.game_over()   # retro-compatibilite si pas de ScreenManager
                
    def get_flags_state(self,scene):
        if scene.current_save.get_flag("jesus"):
            self.can_go_on_water = True
        else:
            self.can_go_on_water = False
    """
    Fonctions pour quitter le jeu
    """
    
    def handle_exit_logic(self, dt, scene):
        """
        gere maintien de l'echap et affichage du texte EXIT
        utilise dans update
        """
        # -- gestion de la sortie (echap)---
        if settings.keys["LEAVE"] not in self.keys:
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
        
        if scene.get_flag("sword_upgrade"):
            SwordClass = SwordSlashUpgrade
        # elif scene.get_flag("fire_sword"):
        #     SwordClass = FireSword
        else:
            SwordClass = SwordSlash
        self.current_sword = SwordClass(self, self.direction)
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
        
        # le 1er son de voix est joue plus souvent
        if random.random() < 0.66:
            voice = "snd_charalongvoice1"
        else: 
            voice = "snd_charalongvoice2"
        scene.sfx_manager.play(voice)
        
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
        
        
    def get_interaction_hitbox(self):
        """
        renvoie la hitbox d'interaction devant le joueur
        """
        px, py, pw, ph = self.get_hitbox()
    
        center_x = px + pw / 2
        center_y = py + ph / 2
        size = settings.tile_size
    
        if self.direction == "up":
            return (
                center_x - size / 2,
                py - size,
                size,
                size * 2
            )
        elif self.direction == "down":
            return (
                center_x - size / 2,
                py,
                size,
                size * 2
            )
        elif self.direction == "left":
            return (
                px - size-(self.hitbox_offset_x*settings.tile_size),
                center_y - size / 2,
                size * 2,
                size
            )
        elif self.direction == "right":
            return (
                px,
                center_y - size / 2,
                size * 2,
                size
            )
        
    
    def rects_overlap(self, a, b): 
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
    
        return (
            ax < bx + bw
            and ax + aw > bx
            and ay < by + bh
            and ay + ah > by
        )
        
    
    def try_interact(self, scene):
        """
        tente interaction avec objet (uniquement avec plus proche si plusieurs)
        """
    
        interact_rect = self.get_interaction_hitbox()
    
        # --- DEBUG HITBOX ---
    
        if DEBUG:
            x, y, w, h = interact_rect
            self.interact_debug_rect.setRect(x, y, w, h)
            if self.interact_debug_rect.scene() is None:
                scene.addItem(self.interact_debug_rect)
    
            self.interact_debug_rect.show()
            # disparition auto apres 0.1s
            temps_hitbox = 0.1 #en s
            QTimer.singleShot(
                temps_hitbox*1000,
                self.interact_debug_rect.hide
            )
    
        # recherche interactable
    
        closest = None
        closest_dist = float("inf")
    
        for interactable in scene.interactables:
            hitbox = interactable.get_hitbox()
            if self.rects_overlap(interact_rect, hitbox):
                dist = self.distance_to(interactable)
                if dist < closest_dist:
                    closest = interactable
                    closest_dist = dist
    
        if closest is not None:
    
            if DEBUG:
                self.interact_debug_rect.hide()
            closest.interact(scene, self)


    def distance_to(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

# Buffs

    def apply_buff(self, duration=DUREE_BUFF):
        """Active le buff de force et vitesse."""
        self._buff_timer = duration
        self.is_buffed = False
        #self.damage = int(self._base_damage * 1.5) + 1
        self.buff_speed_multiplier = 1.5
        self.update_speed()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
        
    
    def update_speed(self):
        self.speed = (
            self._base_speed
            * self.buff_speed_multiplier
            * self.debug_speed_multiplier
        )