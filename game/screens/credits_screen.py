# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt, QTimer, QElapsedTimer

from game.screens.base_screen import BaseScreen
from game.config import Z_SCREEN, TITLE_BG_PATH, interval
from game.fonts import get_font0

class CreditsScreen(BaseScreen):
    """Ecran des credits de fin avec un texte defilant de bas en haut."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self._duration_seconds = 52.0 
        
        self.credits_lines = [
            "FÉLICITATIONS !",
            "Vous avez vaincu Macron !",
            "",
            "--- CRÉDITS ---",
            "",
            "PRODUCTEURS :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "PROGRAMMEURS :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "SCÉNARISTES :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "GAME DESIGN :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "LEVEL DESIGN :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "GRAPHISMES :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "ANIMATIONS :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "MUSIQUES :",
            "Matéo BALDO",
            "",
            "EFFETS SONORES :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "TESTS :",
            "Matéo BALDO",
            "Ryan COLLOT",
            "",
            "REMERCIEMENTS SPÉCIAUX :",
            "À toi d'avoir joué !",
            "",
            "",
            "FIN"
        ]

        self.credits_text_item = None
        self._scroll_timer = None
        self._elapsed_timer = None
        self._start_y = 0
        self._end_y = 0

    def _build(self):
        """Construit le fond et le bloc de texte centre."""
        self._build_background()
        self._build_credits_text()

    def _build_background(self):
        """Reprend exactement le meme fond que l'ecran titre."""
        pix = QPixmap(TITLE_BG_PATH)
        if not pix.isNull():
            bg = QGraphicsPixmapItem(
                pix.scaled(self.scene_w, self.scene_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        else:
            bg = QGraphicsRectItem(0, 0, self.scene_w, self.scene_h)
            bg.setBrush(QBrush(QColor(10, 10, 30)))
            bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(Z_SCREEN)
        self._items.append(bg)

    def _build_credits_text(self):
        """Crée le bloc de texte complet, formate et centre."""
        full_text = "\n".join(self.credits_lines)
        
        self.credits_text_item = QGraphicsTextItem(full_text)
        self.credits_text_item.setFont(get_font0(size=12))
        self.credits_text_item.setDefaultTextColor(QColor(255, 215, 0))
        self.credits_text_item.setZValue(Z_SCREEN + 1)
        
        # Centrage horizontal identique a TitleScreen
        self.credits_text_item.setTextWidth(self.scene_w)
        option = self.credits_text_item.document().defaultTextOption()
        option.setAlignment(Qt.AlignHCenter)
        self.credits_text_item.document().setDefaultTextOption(option)
        
        # Position initiale hors-écran (en bas)
        self.credits_text_item.setPos(0, self.scene_h)
        self._items.append(self.credits_text_item)

    def show(self, scene):
        """Déclenche l'affichage et démarre la boucle de defilement."""
        super().show(scene)
        self._start_scrolling()

    def hide(self):
        """Arrete les timers quand on quitte l'ecran."""
        super().hide()
        if self._scroll_timer and self._scroll_timer.isActive():
            self._scroll_timer.stop()

    def _start_scrolling(self):
        """Initialise les parametres geometriques et temporels du defilement."""
        self._start_y = self.scene_h
        
        # On calcule la hauteur totale du texte pour savoir quand il a fini de sortir par le haut
        text_height = self.credits_text_item.boundingRect().height()
        self._end_y = -text_height
        
        # Placement initial
        self.credits_text_item.setPos(0, self._start_y)
        
        # Configuration des Timers de rafraichissement
        self._elapsed_timer = QElapsedTimer()
        self._elapsed_timer.start()
        
        self._scroll_timer = QTimer()
        self._scroll_timer.setInterval(interval)  #60 fps
        self._scroll_timer.timeout.connect(self._update_scroll)
        self._scroll_timer.start()

    def _update_scroll(self):
        """Met a jour la position Y en fonction du temps ecoule."""
        elapsed_ms = self._elapsed_timer.elapsed()
        total_duration_ms = self._duration_seconds * 1000.0
        
        progress = elapsed_ms / total_duration_ms
        
        if progress >= 1.0:
            progress = 1.0
            self._scroll_timer.stop()
            self._play_sfx("snd_thanks")
            self.screen_manager.go_to_title()
            
        # Interpolation lineire de la position Y
        current_y = self._start_y + (self._end_y - self._start_y) * progress
        self.credits_text_item.setPos(0, int(current_y))