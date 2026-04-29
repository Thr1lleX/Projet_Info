
# sword_slash.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPen, QColor
from game.config import TILE_SIZE, DEBUG, SCALE, BASE_TILE_SIZE

import random
import os
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import QUrl
from game.music import MusicManager

from game.animspr import load_animation_sequence, generate_directional_animations

class SwordSlash(QGraphicsPixmapItem):
    def __init__(self, player, direction, duration=0.125):
        super().__init__()

        self.player = player
        self.direction = direction
        self.targets_hit = set()

        self.setZValue(99) #voir doc setZvalue.txt
        
        self.damage = self.player.damage
        
        # --- PARAMETRES D'ANIMATION DE SPRITE ---
        self.pos = (1,1)
        self.size = (3,2)

        
        self.nb_frames = 9
        self.spr = "player/attack/sword" #on prend le chemin a partir du dossier assets
        
        # --- PARAMETRES D'ATTAQUE ---
        """
        Pour definir la hitbox:
            Toutes les hitboxes seront rectangulaires,(logique avec reste du code)
            Il s'agit d'un dictionnaire, qui pour chaque frame va nous indiquer la hitbox.
            On commence a 1, comme pour le loading des sprites car asesprite commence 
            a compter par 1, et on va utiliser aseprite pour definir les boxes.
            sur ton sprite loaded sur aseprite on va pouvoir delimiter les coins de la hitbox
            pour mieux visualer le rectangle on peut utiliser touche m, et dans les stats
            en bas tu as les coordonnes de ton 1er point, et ensuite du 2e
            
            PERSO JE FAIS EN BAS A DROITE PUIS EN HAUT A GAUCHE
            j'ai fait update_hitbox pour que ca marche pour tout format mtn (tant que points opposes ofc)
        """
        
        self.raw_hitbox_data = {
            1: ((23, 28), (45, 19)),
            2: ((23, 25), (40, 9)),
            3: ((19, 24), (34, 8)),
            **{i: ((16,24) , (31,5)) for i in range(4, 8)},
            8: ((24, 24), (10, 7)),
            9: ((18,28) , (0,16)),
        }
        
        # 
        
        
        #----------
        
        # recupere frames ainsi qu'offset
        self.animation_sequence = load_animation_sequence("assets/"+self.spr,self.nb_frames,self.size)
        self.gen_anim_direct = generate_directional_animations(self.animation_sequence, self.pos,self.size)[self.direction]
        self.frames = self.gen_anim_direct["frames"]
        self.offset = self.gen_anim_direct["offset"] #en pxl!
        
         # variables pour animation, pas a t'en soucier
        self.current_frame = 0
        self.anim_timer = 0
        
        self.anim_speed = duration / len(self.frames)

        self.setPixmap(self.frames[self.current_frame])


        
        # paramètres de knockback comme une Entity
        self.knockback = self.player.knockback
        self.duree_knockback = self.player.duree_knockback

        self.debug_rect = QGraphicsRectItem(self)
        self.debug_rect.setPen(QPen(QColor("green"), 1))

        if not DEBUG:
            self.debug_rect.hide()

        self.update_position()
        self.update_hitbox()

    def update_position(self):
        """
        donne la position comme les autres update
        
        CEPENDANT, on va offset la position par rapport à la rotation
        Voir feuilles avec logique, 
        ou sinon juste regarder la formule de generate_directional_animations
        
        qt nous place dans le coin haut-gauche (0,0), coincide avec position du joueur
        donc on doit offset d'un certain nb de tile (convertis en pixels precedemment)
        """

        x = self.player.x + self.offset[0]
        y = self.player.y + self.offset[1]

        self.setPos(x, y)

    def update_hitbox(self):
        """
        donne la hitbox et la retourne et recentre selon la direction (self.direction)
        setRect fais un rectangle pour du (x,y,w,h)
        """
        # +1 pour correspondance entre navigage de frame (0...n-1) et nom frame (1...n)
        data = self.raw_hitbox_data.get(self.current_frame+1) 
    
        if not data:
            self.debug_rect.hide()
            return
        
        (x1, y1), (x2, y2) = data
        
        rot_data1 = self.rotate_point(x1,y1,self.direction)
        rot_data2 = self.rotate_point(x2,y2,self.direction)
        
        x1, y1 = rot_data1[0]
        x2, y2 = rot_data2[0]
        # meme offset pr les deux
        offset_x, offset_y = rot_data1[1]
        x1 += offset_x
        x2 += offset_x
        y1 += offset_y
        y2 += offset_y

        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x1 - x2), abs(y1 - y2)
        
        # c'est ma hitbox, show ssi DEBUG
        self.debug_rect.setRect(
            x * SCALE,
            y * SCALE,
            w * SCALE,
            h * SCALE
        )
        
        if DEBUG:
            self.debug_rect.show()

    def rotate_point(self,x,y,direction):
        """
        Fonction pour rotation autour de 0,0 un point de la hitbox 
        renvoie aussi offset

        Parameters
        ----------
        x : int
            abscisse en pxl.
        y : int
            ordonnee en pxl.
        direction : str
            "up","left","right","down".
        -------
        nouevelles coordonnees + offset.

        """
        # pour la logique fait un dessin, simple a comprendre
        if direction == "up":
            offset = (0,0)
            new_coord = x,y
            return (new_coord,offset)
        elif direction == "left":
            offset = (0,self.size[0]*BASE_TILE_SIZE)
            new_coord = y,-x
            return (new_coord,offset)

        elif direction == "right":
            offset = (self.size[1]*BASE_TILE_SIZE,0)
            new_coord = -y,x
            return (new_coord,offset)
        else:
            offset = (self.size[0]*BASE_TILE_SIZE,self.size[1]*BASE_TILE_SIZE)
            new_coord = -x,-y
            return (new_coord,offset)
        # je sais pas pk on *BASE_TILE_SIZE et pas TILE_SIZE, mais seul qui fonctionnait

    def check_collisions(self, scene):
        """
        Fonction qui va generer knockback au joueur 
        par rapport a position de l'epee et de l'ennemi
        comme si l'ennemi nous avait frappe
        """
        hitbox_zone = self.debug_rect.mapToScene(
            self.debug_rect.rect()
        ).boundingRect()
    
        for item in scene.items(hitbox_zone):
            if (
                hasattr(item, "take_damage")
                and item != self.player
                and item not in self.targets_hit
            ):
                # --- dégâts + knockback ennemi (source = épée) ---
                item.take_damage(scene, self.damage, self)
                item.stun(0)
                self.targets_hit.add(item)
    
                # --- knockback du joueur (recul) ---
                # direction = épée → joueur
                # intensité + durée = ennemi
    
                old_kb = self.knockback
                old_duration = self.duree_knockback
    
                self.knockback = item.knockback
                self.duree_knockback = item.duree_knockback
    
                self.player.get_knockback(scene, self)
    
                # restore
                self.knockback = old_kb
                self.duree_knockback = old_duration
            
    def update(self, dt, scene):
        self.update_position()

        self.anim_timer += dt

        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.current_frame += 1

            if self.current_frame < len(self.frames):
                self.setPixmap(self.frames[self.current_frame])
                self.update_hitbox()
                self.check_collisions(scene)
            else:
                self.die()

    def die(self):
        if self.scene():
            self.scene().removeItem(self)

        self.player.is_attacking = False

        
    def get_center(self):
        rect = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()
        return (rect.center().x(), rect.center().y())
    
