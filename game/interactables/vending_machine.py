# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

from game.interactables.interactable import Interactable
from PyQt5.QtWidgets import QGraphicsPixmapItem,QGraphicsColorizeEffect
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QTimer
from game.settings import settings

class VendingMachine(Interactable):
    """Distributeur automatique permettant d'ameliorer l'epee du joueur."""
    def __init__(self, scale,x,y):
        super().__init__()
        self.x = x
        self.y = y
        self.setPos(self.x, self.y)
        
        sprite_path = "assets/vending_machine.png"
        pixmap = QPixmap(sprite_path)
        
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(
                settings.tile_size * 2, 
                settings.tile_size * 2, 
                transformMode=Qt.FastTransformation
            ))
        
        self.collision = 1
        self.setZValue(90)
        
        self.hitbox_width = self.tile_size * 2
        self.hitbox_height = self.tile_size * 2
        
        self.interact_cooldown = 0
        
        self.machine_loaded = False


    def interact(self, scene, player):
        """Declenche l'amelioration de l'epee si elle n'est pas encore obtenue, ou joue un son."""
        if self.interact_cooldown >= 0:
            return
        
        self.interact_cooldown = 0.9
        # verification si l'amelioration a deja ete obtenue
        if scene.get_flag("sword_upgrade"):
            if self.machine_loaded:
                scene.sfx_manager.play("snd_vending2")
                self.machine_loaded = False
            else:
                scene.sfx_manager.play("snd_vending1")
                self.machine_loaded = True
            return

        # activation du flag sinon
        scene.session_flags["sword_upgrade"] = True

        # effets visuels et sonores
        scene.sfx_manager.play("snd_upgrade")

        player.is_cinematic = True
        QTimer.singleShot(900, lambda: setattr(player, "is_cinematic", False))

        white_effect = QGraphicsColorizeEffect()
        white_effect.setColor(QColor("white"))
        white_effect.setStrength(1.0) # 1.0 est l'alpha
        
        player.setGraphicsEffect(white_effect)

        QTimer.singleShot(150, lambda: player.setGraphicsEffect(None)) #0.5
        scene.dialogue_manager.start_text('', font="font2") #c'est fait expres
            
    def update(self, dt,scene):
        """Gere le temps de rechargement entre chaque interaction."""
        self.interact_cooldown -= dt