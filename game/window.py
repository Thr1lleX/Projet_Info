# -*- coding: utf-8 -*-
import sys
import os

from PyQt5.QtWidgets import QGraphicsView, QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from game.scene import GameScene, TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT
from game.config import DEBUG


class GameWindow(QGraphicsView):
    def __init__(self):
        super().__init__()
        
        
        width = GRID_WIDTH * TILE_SIZE
        height = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

        self.setFixedSize(width, height)

        self.scene = GameScene()
        self.setScene(self.scene)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # # ===== FOCUS =====
        # self.setFocusPolicy(Qt.StrongFocus)
        # self.setFocus()

    def keyPressEvent(self, event):
        self.scene.keyPressEvent(event)
        self.scene.player.key_press(event.key())

    def keyReleaseEvent(self, event):
        self.scene.keyReleaseEvent(event)
        self.scene.player.key_release(event.key())
        

    def closeEvent(self, event):
        if hasattr(self, "scene"):
            if hasattr(self.scene, "music_manager"):
                self.scene.music_manager.stop()
    
        event.accept()
        


    def quitter_jeu(self):
        if DEBUG:
            print("Demande de fermeture de l'application...")
        
        if hasattr(self, 'scene') and hasattr(self.scene, 'music_manager'):
            self.scene.music_manager.stop()
            
        # ferme fenetre
        self.close()

        # arret de PyQt
        QCoreApplication.quit()
