# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPen, QColor

from game.sfx import SFXManager

from game.attacks.attack_entity import MeleeAttack

class Spear(MeleeAttack):
    def __init__(self, player, direction):
        
        # --- PARAMETRES DE DEFINITION POUR APPEL A CLASSES ANTERIEURES ---
        self.source = player
        self.direction = direction

        self.damage = self.source.damage
        
        self.pos = (0,3)
        self.size = (1,4)
        
        self.nb_frames = 7
        self.spr = "player/attack/spear" #on prend le chemin a partir du dossier assets

        super().__init__(source = player, 
                         direction = direction, 
                         damage=self.damage, 
                         duration=0.8,
                         spr_path = self.spr,
                         nb_frames = self.nb_frames,
                         size = self.size,
                         pos = self.pos 
        )
        
        # --- PARAMETRES D'ATTAQUE ---
        # oblige de mettre apres super init car sinon recup parametres de base
        self.give_player_knockback = False
        self.do_stun = 10  # 0 = aucun stun, x = duree
        
        self.knockback = self.source.knockback # en tiles
        self.duree_knockback = self.source.duree_knockback
        
        self.targets_hit = set()

        
        # --- PARAMETRES D'ATTAQUE ---
        self.raw_hitbox_data = {
            1: ((2, 63), (13, 30)),
            2: ((2, 64), (13, 31)),
            3: ((2, 50), (13, 16)),
            4: ((0, 51), (16, 13)),
            5: ((0, 51), (16, 0)),
            6: ((0, 51), (16, 12)),
            7: ((2, 50), (13, 16))
        }
        
        self.debug_rect.setPen(QPen(QColor("green"), 1))
    
        self.update_hitbox()


    # ------
        
    def die(self):
        if self.scene():
            self.scene().removeItem(self)

        self.source.is_usingspear = False

