# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPen, QColor

from game.sfx import SFXManager

from game.attacks.attack_entity import MeleeAttack

class SwordSlash(MeleeAttack):
    def __init__(self, player, direction, spr_path=None):
        
        # --- PARAMETRES DE DEFINITION POUR APPEL A CLASSES ANTERIEURES ---
        self.source = player
        self.direction = direction

        self.damage = self.source.damage
        
        # position du joueur sur sprite sheet
        self.pos = (1,1)
        # taille du sprite sheet en tiles
        self.size = (3,2)
        
        self.nb_frames = 9
        self.spr = spr_path if spr_path else "player/attack/sword"
        #on prend le chemin a partir du dossier assets

        super().__init__(source = player, 
                         direction = direction, 
                         damage=self.damage, 
                         duration=0.125,
                         spr_path = self.spr,
                         nb_frames = self.nb_frames,
                         size = self.size,
                         pos = self.pos 
        )
        
        # --- PARAMETRES D'ATTAQUE ---
        # oblige de mettre apres super init car sinon recup parametres de base
        self.give_player_knockback = True
        self.do_stun = 0  # 0 = aucun stun, x = duree
        
        self.knockback = self.source.knockback # en tiles
        self.duree_knockback = self.source.duree_knockback
        
        self.targets_hit = set()

        
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
        
        self.debug_rect.setPen(QPen(QColor("green"), 1))

        self.update_hitbox()
        
    # ------
    # mdr il reste le def die a la fin, j'arrive pas a le mettre dans AttackEntity
    # sans faire 50 disjonctions de cas

    def die(self):
        if self.scene():
            self.scene().removeItem(self)

        self.source.is_attacking = False
