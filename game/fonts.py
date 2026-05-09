# -*- coding: utf-8 -*-
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

# dictionnaire qui sotcke les polices une fois chargees, on ne les charge pas avant sinon Access Violation
_fonts = {}

def get_font(path, size=10, bold=False):
    """
    charger la police lorsque invoquee. 
    """
    if path not in _fonts:
        # On vérifie si une QApplication existe, sinon on ne peut pas charger de police
        if not QApplication.instance():
            return QFont("Arial", size, QFont.Bold if bold else QFont.Normal)

        font_id = QFontDatabase.addApplicationFont(path)
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            _fonts[path] = family
        else:
            # securite, on charge arial si le fichier n'est pas detecte
            print(f"Erreur : Impossible de charger {path}")
            _fonts[path] = "Arial"

    font = QFont(_fonts[path], size)
    if bold:
        font.setBold(True)
    return font

# exemple de fonts

from game.config import SCALE

def get_font0(size=10):
    return get_font("fonts/8bitoperator.ttf", int(size*SCALE)) # Pour que le changement de scale permette de modif la police

def get_font1(size=10):
    return get_font("fonts/undertale-wingdings.ttf", int(size*SCALE))

def get_font2(size=10):
    return get_font("fonts/earthbound-beginnings.ttf", int(size*SCALE))

FONT_MAPPING = {
    "font0": get_font0,
    "font1": get_font1,
    "font2": get_font2
}