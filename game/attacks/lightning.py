# -*- coding: utf-8 -*-
from game.attacks.attack_entity import TemporaryAttack
from game.animspr import load_animation_sequence
from game.settings import settings

class Lightning(TemporaryAttack):
    def __init__(self, source, x, y):
        # L'attaque dure 0.75s au total (15 frames * 0.05s)
        super().__init__(source=source, direction="down", damage=1.5, duration=0.75)
        
        self.x = x
        self.y = y
        self.setPos(self.x, self.y)
        
        self.nb_frames = 15
        self.size = (1, 1)
        self.anim_offset = (0, 0)
        
        self.frames = load_animation_sequence("assets/enemies/polasu/lightning", self.size, self.nb_frames)
        self.current_frame = 0
        
        # 0.05s = 50ms par frame
        self.anim_speed = 0.05 
        
        # Hitboxes (Aseprite compte à partir de 1)
        self.raw_hitbox_data = {
            4: ((4, 15), (11, 4)),
            5: ((1, 15), (14, 0)),
            6: ((0, 15), (15, 0)),
            7: ((0, 15), (15, 0)),
            8: ((2, 15), (14, 0)),
            9: ((2, 15), (14, 0)),
            10: ((4, 15), (10, 0)),
            11: ((4, 15), (10, 0)),
            12: ((4, 15), (10, 0))
        }
        
        self.setPixmap(self.frames[self.current_frame])
        self.update_hitbox()

    def update_hitbox(self):
        super().update_hitbox()
        # Correction du "hitbox persistante" : on force un rectangle nul si pas de hitbox sur cette frame
        data = self.raw_hitbox_data.get(self.current_frame + 1)
        if not data:
            self.debug_rect.setRect(0, 0, 0, 0)

    def die(self):
        if self.scene():
            self.scene().removeItem(self)