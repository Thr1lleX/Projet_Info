# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPen, QColor
from game.attacks.attack_entity import MeleeAttack

class SwordShadow(MeleeAttack):
    """Attaque d'epee utilisee par l'ennemi Shadow."""
    def __init__(self, shadow_entity, direction,damage=1):
        
        self.source = shadow_entity
        self.direction = direction

        self.damage = damage
        
        # position du joueur sur sprite sheet
        self.pos = (1,1)
        # taille du sprite sheet en tiles
        self.size = (3,2)
        
        self.nb_frames = 9
        self.spr = "enemies/shadow/sword"
        self.player = self.source.target
        #on prend le chemin a partir du dossier assets

        super().__init__(source = shadow_entity, 
                         direction = direction, 
                         damage=self.damage, 
                         duration=0.125,
                         spr_path = self.spr,
                         nb_frames = self.nb_frames,
                         size = self.size,
                         pos = self.pos 
        )
        
        # --- PARAMETRES D'ATTAQUE ---
        self.give_player_knockback = False
        self.do_stun = 0
        
        self.knockback = self.player.knockback
        self.duree_knockback = self.player.duree_knockback

        
        # --- PARAMETRES D'ATTAQUE ---
        
        self.raw_hitbox_data = {
            1: ((23, 28), (45, 19)),
            2: ((23, 25), (40, 9)),
            3: ((19, 24), (34, 8)),
            **{i: ((16,24) , (31,5)) for i in range(4, 8)},
            8: ((24, 24), (10, 7)),
            9: ((18,28) , (0,16)),
        }
        
        self.debug_rect.setPen(QPen(QColor("green"), 1))

        self.update_hitbox()
        
    def die(self):
        """Supprime l'epee et libere l'etat d'attaque de l'ennemi."""
        if self.scene():
            self.scene().removeItem(self)

        self.source.is_attacking = False