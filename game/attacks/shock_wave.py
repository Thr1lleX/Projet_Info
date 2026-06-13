# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPen, QColor
from game.attacks.attack_entity import TemporaryAttack
from game.animspr import load_animation_sequence
from game.settings import settings

class ShockWave(TemporaryAttack):
    def __init__(self, source, direction="down"):
        # L'attaque dure 3.0s au total
        super().__init__(source=source, direction=direction, damage=2, duration=2.5)
        
        # Position de base (on s'accroche au boss)
        self.x = source.x
        self.y = source.y
        
        # --- CENTRAGE ---
        # Le boss fait 2x2, l'attaque 4x4. 
        # Pour centrer, on décale l'attaque de 1 tile vers la gauche et le haut (-1, -1)
        self.anim_offset = (-1 * settings.tile_size, -1 * settings.tile_size)
        self.setPos(self.x + self.anim_offset[0], self.y + self.anim_offset[1])
        
        self.nb_frames = 12
        self.size = (4, 4)
        
        # Chargement manuel des frames (géré automatiquement dans MeleeAttack, mais ici on le fait à la main)
        self.frames = load_animation_sequence("assets/enemies/bras_droit/shock_wave", self.size, self.nb_frames)
        self.current_frame = 0
        
        # Vitesse d'animation = durée totale (3.0s) divisée par le nombre de frames (12) = 0.25s / frame
        self.anim_speed = self.duration / self.nb_frames 
        
        # --- PARAMETRES D'ATTAQUE ---
        self.give_player_knockback = False
        self.do_stun = 0
        self.targets_hit = set()
        
        # Nouvelles hitboxes
        self.raw_hitbox_data = {
            5: ((15, 48), (48, 15)),
            6: ((11, 51), (51, 11)),
            **{i: ((2, 60), (60, 2)) for i in range(7, 9)},
            **{i: ((0, 64), (64, 0)) for i in range(9, 12)}
        }
        
        self.setPixmap(self.frames[self.current_frame])
        self.debug_rect.setPen(QPen(QColor("green"), 1))
        
        # Appel initial pour set la hitbox de la première frame (vide)
        self.update_hitbox()

    def update_hitbox(self):
        super().update_hitbox()
        # Sécurité cruciale (comme dans Lightning) : 
        # Si la frame actuelle n'a pas de hitbox dans raw_hitbox_data, on la réduit à néant.
        data = self.raw_hitbox_data.get(self.current_frame + 1)
        if not data:
            self.debug_rect.setRect(0, 0, 0, 0)

    def die(self):
        if self.scene():
            self.scene().removeItem(self)
        self.source.is_attacking = False