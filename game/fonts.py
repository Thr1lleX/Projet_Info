# -*- coding: utf-8 -*-
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication
from game.config import SCALE


# dictionnaire qui sotcke les polices une fois chargees, on ne les charge pas avant sinon Access Violation
_fonts = {}

SYSTEM_SCALE = 1.0
app = QApplication.instance()
if app:
    try:
        screen = app.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            # 96 DPI = 100%
            if dpi and dpi > 0:
                SYSTEM_SCALE = dpi / 96.0

    except Exception:
        SYSTEM_SCALE = 1.0


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
            
    final_size = int(size*SCALE/ SYSTEM_SCALE)

    font = QFont(_fonts[path], final_size)
    if bold:
        font.setBold(True)
    return font


def get_font0(size=10):
    return get_font("fonts/8bitoperator.ttf", size) # Pour que le changement de scale permette de modif la police

def get_font1(size=10):
    return get_font("fonts/undertale-wingdings.ttf", size)

def get_font2(size=10):
    return get_font("fonts/earthbound-beginnings.ttf", size)

FONT_MAPPING = {
    "font0": get_font0,
    "font1": get_font1,
    "font2": get_font2
}