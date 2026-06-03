# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication
from game.settings import settings


# dictionnaire qui sotcke les polices une fois chargees, on ne les charge pas avant sinon Access Violation
_fonts = {}

SYSTEM_SCALE = None


def get_system_scale():
    """
    on recupere directement ici car sinon q application pas encore cree
    (sous spyder, conserve les variables apres fermeture du programme, mais pas autres ide)
    """
    global SYSTEM_SCALE

    if SYSTEM_SCALE is not None:
        return SYSTEM_SCALE

    SYSTEM_SCALE = 1.0

    app = QApplication.instance()

    if not app:
        return SYSTEM_SCALE
    
    try:
        screen = app.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            # 96 DPI = 100%
            if dpi and dpi > 0:
                SYSTEM_SCALE = dpi / 96.0

    except Exception:
        SYSTEM_SCALE = 1.0

    return SYSTEM_SCALE


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
    
    SYSTEM_SCALE = get_system_scale()
    final_size = int(size*settings.scale/ SYSTEM_SCALE)

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
def get_font3(size=10):
    return get_font("fonts/Greek Font.ttf", 1.1*size)
def get_font4(size=10):
    return get_font("fonts/moi font.ttf", 1.1*size)



FONT_MAPPING = {
    "font0": get_font0,
    "font1": get_font1,
    "font2": get_font2,
    "font3": get_font3,
    "font4": get_font4
}
