# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QMovie, QIcon
from PyQt5.QtCore import Qt
import os


class RickWindow(QWidget):
    def __init__(self, music_manager):
        super().__init__()

        self.music_manager = music_manager
        
        # moment maturite
        self.setWindowTitle("get dunked on nerd!")        
        self.setWindowIcon(QIcon('assets/troll.png'))
        
        self.setFixedSize(420, 498)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        gif_path = os.path.abspath("assets/rick.gif")

        self.movie = QMovie(gif_path)
        self.label.setMovie(self.movie)

        self.movie.start()

        # lancer la musique
        self.music_manager.stop()
        self.music_manager.play("mus_rick")

    def closeEvent(self, event):
        # stop musique quand on ferme
        self.music_manager.stop()
        event.accept()