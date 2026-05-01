# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 12:25:20 2026

@author: mateo
"""
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from game.window import GameWindow
from game.screen_manager import ScreenManager
from game.screens.title_screen import TitleScreen
from game.screens.game_over_screen import GameOverScreen
from game.screens.settings_screen import SettingsScreen
from game.screens.pause_screen import PauseScreen
from game.screens.inventory_screen import InventoryScreen
from game.settings_manager import SettingsManager
from game.item import Inventory
from game.config import GAME_TITLE



def main():
    app = QApplication(sys.argv)

    window = GameWindow()

    # creation du gestionnaire d'ecrans
    sm = ScreenManager(window)

    # parametres persistants et inventaire
    sm.settings  = SettingsManager()
    sm.inventory = Inventory(total_slots=30)

    # enregistrement des ecrans
    sm.register_screen("title",     TitleScreen(sm))
    sm.register_screen("game_over", GameOverScreen(sm))
    sm.register_screen("settings",  SettingsScreen(sm))
    sm.register_screen("pause",     PauseScreen(sm))
    sm.register_screen("inventory", InventoryScreen(sm))

    # injection du screen_manager dans la fenetre
    window.screen_manager = sm

    # demarre sur l'ecran titre (cree la premiere scene en pause)
    sm.go_to_title()

    # application des parametres de fenetre (plein ecran au demarrage si configure)
    sm.settings.apply_to_window(window)

    window.setWindowTitle(GAME_TITLE)
    window.setWindowIcon(QIcon('assets/logo.png'))
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
