# -*- coding: utf-8 -*-

from game.interactables.npc import NPC
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from game.config import SCALE, TILE_SIZE

class Sign(NPC):
    def __init__(self, scale, x, y, dialogue_id=None,conditional_rules=None):
        super().__init__(scale, x, y, npc_type=None, dialogue_id=dialogue_id,conditional_rules=conditional_rules)
        self.collision = 1
        self.type = "sign"
        
        pixmap = QPixmap("assets/sign.png")
        if not pixmap.isNull():
            # On passe les arguments directement, sans les nommer
            self.setPixmap(pixmap.scaled(
                int(TILE_SIZE), 
                int(TILE_SIZE),
                Qt.IgnoreAspectRatio,
                Qt.FastTransformation
            ))
        
        self.update_graphics()

    def update(self, dt):
        # ecrase methode car image statique
        pass