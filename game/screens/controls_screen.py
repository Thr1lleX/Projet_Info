# -*- coding: utf-8 -*-

# Auteur : essentiellement Matéo


"""Gestion de la transition d'ecran puis affichage des controles."""

from PyQt5.QtWidgets import QGraphicsObject
from PyQt5.QtGui import QLinearGradient, QPainter, QColor, QBrush
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5 import QtCore

class WipeOverlay(QGraphicsObject):
    def __init__(self, width, height):
        super().__init__()
        self.w = width
        self.h = height
        self._progress = 0.0  # 0: tout noir, 1: tout visible
        self.feather = 0.15   # Largeur du bord doux (15% de l'écran)
        self.invert = False   # Pour l'animation de fermeture
        self.setZValue(Z_SCREEN + 5)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.w, self.h)

    # on met la methode comme un objet de qt 
    @pyqtProperty(float)
    def progress(self): return self._progress
    @progress.setter
    def progress(self, v):
        self._progress = v
        self.update()

    def paint(self, painter, option, widget):
        painter.setPen(QtCore.Qt.NoPen)
        grad = QLinearGradient(0, 0, 0, self.h)
        
        p = self._progress
        f = self.feather

        if not self.invert:
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(max(0, min(1, p - f)), QColor(0, 0, 0, 0))
            grad.setColorAt(max(0, min(1, p)), QColor(0, 0, 0, 255))
            grad.setColorAt(1, QColor(0, 0, 0, 255))
        else:
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(max(0, min(1, p)), QColor(0, 0, 0, 0))
            grad.setColorAt(max(0, min(1, p + f)), QColor(0, 0, 0, 255))
            grad.setColorAt(1, QColor(0, 0, 0, 255))

        painter.setBrush(QBrush(grad))
        painter.drawRect(self.boundingRect())


from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QColor, QKeySequence, QPen
from PyQt5.QtCore import Qt

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN
from game.fonts import get_font0

from game.settings import settings

class ControlsScreen(BaseScreen):
    """Ecran affichant les touches de controle du jeu avant le lancement d'une partie."""
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self.actions = [
            {"label": "Se déplacer", "key_cfg": None}, # exception car icone
            {"label": "Interagir",   "key_cfg": "INTERACT"},
            {"label": "Attaquer",    "key_cfg": "ATTACK"},
            {"label": "Objet",       "key_cfg": "ITEM"},
            {"label": "Inventaire",  "key_cfg": "INVENTORY"},
            {"label": "Pause",       "key_cfg": "PAUSE"},
            {"label": "Quitter",     "key_cfg": "LEAVE"},
        ]

    def _build(self):
        """Cree les elements graphiques (fond, cadre, icones et textes des touches)."""
        # Background noir
        bg_black = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
        bg_black.setBrush(QColor(0, 0, 0))
        bg_black.setPen(QPen(Qt.NoPen))
        bg_black.setZValue(Z_SCREEN)
        self._items.append(bg_black)

        # Cadre en 16x13
        pix_frame = QPixmap(r"assets\hud\hud_demarrage.png")
        if not pix_frame.isNull():
            frame = QGraphicsPixmapItem(pix_frame.scaled(self.scene_w, self.scene_h))
            frame.setZValue(Z_SCREEN + 1)
            self._items.append(frame)

        # lignes
        start_x = 2 * settings.tile_size
        start_y = 1.25 * settings.tile_size
        box_size = 1.25 * settings.tile_size
        spacing = 1.5 * settings.tile_size 
        # (1.25 de boite + 0.25 d'ecart)

        pix_box = QPixmap(r"assets\hud\hud_box_demarrage.png")
        
        for i, info in enumerate(self.actions):
            current_y = start_y + (i * spacing)
            
            # boites
            if not pix_box.isNull():
                box = QGraphicsPixmapItem(pix_box.scaled(int(box_size), int(box_size)))
                box.setPos(start_x, current_y)
                box.setZValue(Z_SCREEN + 3)
                self._items.append(box)

            # contenu dans boite
            if i == 0:
                # icone de deplacement
                pix_move = QPixmap(r"assets\hud\hud_icone_deplacement.png")
                if not pix_move.isNull():
                    icon = QGraphicsPixmapItem(pix_move.scaled(settings.tile_size, settings.tile_size))
                    # centrage
                    offset = (box_size - settings.tile_size) / 2
                    icon.setPos(start_x + offset, current_y + offset)
                    icon.setZValue(Z_SCREEN + 3)
                    self._items.append(icon)
            else:
                # texte de la tocuhe
                key_str = QKeySequence(settings.keys[info["key_cfg"]]).toString()
                key_text = QGraphicsTextItem(key_str)
                key_text.setFont(get_font0(5.5))
                key_text.setDefaultTextColor(QColor(255, 255, 255))
                
                # Centrage
                bw = key_text.boundingRect().width()
                bh = key_text.boundingRect().height()
                key_text.setPos(start_x + (box_size - bw)/2, current_y + (box_size - bh)/2)
                key_text.setZValue(Z_SCREEN + 2)
                self._items.append(key_text)

            # texte de description
            action_text = QGraphicsTextItem(info["label"])
            action_text.setFont(get_font0(9))
            action_text.setDefaultTextColor(QColor(255, 255, 255))
            # alignement
            action_text.setPos(start_x + box_size + settings.tile_size, current_y)
            action_text.setZValue(Z_SCREEN + 2)
            self._items.append(action_text)
            
    
    def show(self, scene):
        """Affiche l'ecran et lance l'animation de transition (wipe) a l'ouverture."""
        super().show(scene)
        
        # recreation du wipe (cas ou plusieurs parties lancees)
        if hasattr(self, "wipe_item"):
            try:
                if self.wipe_item.scene():
                    self.wipe_item.scene().removeItem(self.wipe_item)
            except RuntimeError:
                pass
        
        self.wipe_item = WipeOverlay(self.scene_w, self.scene_h)
        self._items.append(self.wipe_item)
        scene.addItem(self.wipe_item)
        
        self.is_closing = False
        
        self.wipe_item.invert = False
        self.wipe_item.setOpacity(1.0)
        
        self.wipe_item.progress = 0.0
        
        self.anim = QPropertyAnimation(self.wipe_item, b"progress")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.15) # 1.15 pour depasser avec le bord doux
        self.anim.start()
        
        self._play_sfx("snd_gamecontrols")


    def key_press(self, key):
        """Gere la validation pour fermer l'ecran et demarrer la partie avec une transition."""
        # empeche spam durant animation
        if self.is_closing: return 
        
        if key in (settings.keys["INTERACT"], settings.keys["CONFIRM"]):
            self.is_closing = True
            self._play_sfx("snd_lancement")
            
            # Animation de fermeture (1s) : le noir remonte depuis le bas
            self.wipe_item.invert = True
            self.wipe_item.progress = 0.999
            self.wipe_item.update()
            self.anim = QPropertyAnimation(self.wipe_item, b"progress")
            self.anim.setDuration(1000)
            
            self.anim.setStartValue(0.999)
            self.anim.setEndValue(-0.15)
            self.anim.finished.connect(self._on_close_finished)
            self.anim.start()

    def _on_close_finished(self):
        """Finalise la fermeture de l'ecran apres l'animation de transition."""
        # s'assurer que bien noir avant de switcher
        self.wipe_item.progress = -0.15
        # Une fois l'écran noir, on lance la partie avec le fondu final de 0.2s
        self.screen_manager.finalize_new_game(self.wipe_item)