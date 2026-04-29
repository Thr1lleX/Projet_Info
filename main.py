# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 12:25:20 2026

@author: mateo
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from game.window import GameWindow

def main():
    app = QApplication(sys.argv)

    window = GameWindow()
    window.setWindowTitle('game_title')
    window.setWindowIcon(QIcon('assets/logo.png'))

    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
