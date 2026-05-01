# -*- coding: utf-8 -*-
import sys

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PyQt5.QtCore import Qt, QCoreApplication

from game.config import (
    TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, DEBUG,
)


class GameWindow(QGraphicsView):
    """
    Fenetre principale du jeu (QGraphicsView).

    Responsabilites :
      - Dimensionner la fenetre.
      - Router les evenements clavier vers le ScreenManager (si un ecran est actif)
        ou vers la scene de jeu (sinon).
      - Router les clics souris vers le ScreenManager si un ecran est actif.
      - Fermer proprement l'application.

    La scene de jeu (GameScene) est injectee par le ScreenManager via setScene(),
    et non plus creee ici. Cela permet de swapper la scene en cours de session.
    """

    def __init__(self):
        super().__init__()
        # + 2 car ajoute un pixel de chaque coté (sinon y'a un decalage et fenetre peut bouger)
        width  = GRID_WIDTH  * TILE_SIZE + 2
        height = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE + 2
        self.setFixedSize(width, height)

        # scene vide en attendant l'initialisation par ScreenManager
        self.setScene(QGraphicsScene())

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # defini par main.py apres construction
        self.screen_manager = None

    # ------------------------------------------------------------------
    # clavier
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        # si un ecran de menu est actif, il consomme la touche
        if self.screen_manager and self.screen_manager.route_key_press(event.key()):
            return

        # comportement normal pendant le jeu
        scene = self.scene()
        if hasattr(scene, 'keyPressEvent'):
            scene.keyPressEvent(event)
        if hasattr(scene, 'player'):
            scene.player.key_press(event.key())

    def keyReleaseEvent(self, event):
        # si un ecran est actif, absorber le key_release pour eviter les fuites
        if self.screen_manager and self.screen_manager.route_key_release(event.key()):
            return

        scene = self.scene()
        if hasattr(scene, 'keyReleaseEvent'):
            scene.keyReleaseEvent(event)
        if hasattr(scene, 'player'):
            scene.player.key_release(event.key())

    # ------------------------------------------------------------------
    # souris
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if self.screen_manager:
            scene_pos = self.mapToScene(event.pos())
            if self.screen_manager.route_mouse_press(scene_pos):
                return
        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # fermeture
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        scene = self.scene()
        if hasattr(scene, 'timer'):
            scene.timer.stop()
        if hasattr(scene, 'music_manager'):
            scene.music_manager.stop()
        event.accept()

    def quitter_jeu(self):
        if DEBUG:
            print("Fermeture de l'application...")

        scene = self.scene()
        if hasattr(scene, 'timer'):
            scene.timer.stop()
        if hasattr(scene, 'music_manager'):
            scene.music_manager.stop()

        self.close()
        QCoreApplication.quit()
