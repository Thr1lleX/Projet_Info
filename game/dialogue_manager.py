# -*- coding: utf-8 -*-

import json

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem

from PyQt5.QtGui import QPixmap,QColor

from PyQt5.QtCore import Qt

from game.config import SCALE, TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT
from game.fonts import *

from game.config import DEBUG, KEYS


class DialogueManager:
    """
    Gestionnaire principal des dialogues:
        - charger dialogues.json
        - afficher boite de dialogue
        - afficher texte lettre par lettre avec son
        - gerer les lignes
        - gerer fermeture dialogue
    """

    def __init__(self, scene):

        self.scene = scene

        self.active = False

        self.current_dialogue_id = None
        self.current_dialogue = None

        self.current_line_index = 0

        # texte
        self.full_text = ""
        self.displayed_text = ""

        # animation texte
        self.current_char_index = 0
        self.char_timer = 0

        self.base_text_speed = 30 #char/s
        self.text_speed_delay = 1.0 / self.base_text_speed

        # police active
        self.current_font = get_font0(size=7.5)

        # -------------------------
        # chargement dialogues
        # -------------------------

        with open("dialogues.json", "r", encoding="utf-8") as f:
            self.dialogues = json.load(f)

        # -------------------------
        # boite de dialogue
        # -------------------------

        self.box = QGraphicsPixmapItem()

        pix = QPixmap("assets/hud/dialogue_box.png")

        width = GRID_WIDTH * TILE_SIZE
        height = 5 * TILE_SIZE

        self.box.setPixmap(
            pix.scaled(
                width,
                height,
                Qt.IgnoreAspectRatio,
                Qt.FastTransformation
            )
        )

        Zvalue = 1010
        self.box.setZValue(Zvalue)

        # position en bas ecran
        self.box.setPos(
            0,
            (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE - height
        )

        # -------------------------
        # texte
        # -------------------------

        self.text_item = QGraphicsTextItem()

        self.text_item.setDefaultTextColor(
            QColor("white")
        )

        self.text_item.setZValue(Zvalue+1)

        # largeur max du texte
        self.text_item.setTextWidth(
            width - (2 * TILE_SIZE)
        )

        self.text_item.setPos(
            TILE_SIZE,
            self.box.y() + TILE_SIZE * 0.65
        )

    # ==========================================================
    # démarrage dialogue
    # ==========================================================

    def start(self, dialogue_id):
        if dialogue_id not in self.dialogues and DEBUG:
            print(f"Dialogue introuvable : {dialogue_id}")
            return

        self.active = True

        self.current_dialogue_id = dialogue_id
        self.current_dialogue = self.dialogues[dialogue_id]
        self.current_line_index = 0
        
        # par defaut font0
        font_name = self.current_dialogue.get("font", "font0")
        font_func = FONT_MAPPING.get(font_name, FONT_MAPPING["font0"])

        self.current_font = font_func(size=7.5)
        
        self.text_item.setFont(self.current_font)

        # vitesse texte
        chars_per_second = self.current_dialogue.get("speed", self.base_text_speed)
        self.text_speed_delay = 1.0 / chars_per_second


        # ajout scene
        if self.box.scene() is None:
            self.scene.addItem(self.box)

        if self.text_item.scene() is None:
            self.scene.addItem(self.text_item)

        self._load_current_line()

    # ==========================================================
    # chargement ligne
    # ==========================================================

    def _load_current_line(self):

        lines = self.current_dialogue["lines"]

        if self.current_line_index >= len(lines):
            self.close()
            return

        self.full_text = lines[self.current_line_index]

        self.displayed_text = ""

        self.current_char_index = 0
        self.char_timer = 0

        self.text_item.setPlainText("")

    # ==========================================================
    # update animation texte
    # ==========================================================


    def update(self, dt):
        if not self.active:
            return
    
        if not self.active or self.current_char_index >= len(self.full_text):
            if hasattr(self.scene, 'player') and KEYS["ITEM"] in self.scene.player.keys:
                self.advance()
            return
        
        markiplier = 1.0
        if hasattr(self.scene, 'player') and KEYS["ITEM"] in self.scene.player.keys:
            markiplier = 10.0
            
        current_delay = self.text_speed_delay / markiplier
        
        # variable pour empecher spam de bip lorsque accelere le texte
        sound_played_this_frame = False
    
        self.char_timer += dt
    
        while self.char_timer >= current_delay:
            self.char_timer -= current_delay
            self.current_char_index += 1
    
            self.displayed_text = self.full_text[:self.current_char_index]
            self.text_item.setPlainText(self.displayed_text)
    
            # on ne joue le son que si on n'est pas sur un espace vide
            char = self.full_text[self.current_char_index - 1]
            if char.strip() and hasattr(self.scene, "sfx_manager"):
                if not sound_played_this_frame:
                    self.scene.sfx_manager.play("snd_text_blip")
                    sound_played_this_frame = True
    
            if self.current_char_index >= len(self.full_text):
                break

    # ==========================================================
    # interaction joueur
    # ==========================================================

    def advance(self):
        """
        appelee quand joueur appuie sur INTERACT
        """

        if not self.active:
            return

        # texte pas fini, affiche instantanément
        if self.current_char_index < len(self.full_text):

            self.current_char_index = len(self.full_text)

            self.displayed_text = self.full_text

            self.text_item.setPlainText(
                self.displayed_text
            )

            return

        # ligne suivante
        self.current_line_index += 1
        lines = self.current_dialogue["lines"]

        if self.current_line_index >= len(lines):

            # flag eventuel
            flags_data = self.current_dialogue.get("set_flag")
            
            if flags_data and hasattr(self.scene,"current_save"):
                if isinstance(flags_data, str):
                    flags_list = [flags_data]
                elif isinstance(flags_data, list):
                    flags_list = flags_data
                else:
                    flags_list = []
                
                for f in flags_list:
                    self.scene.current_save.data["flags"][f] = True
                    if DEBUG: print(f"[DIALOGUE] Flag activé : {f}")

            self.close()
            return

        self._load_current_line()

    # ==========================================================
    # fermeture
    # ==========================================================

    def close(self):

        self.active = False
        

        if self.box.scene():
            self.scene.removeItem(self.box)

        if self.text_item.scene():
            self.scene.removeItem(self.text_item)

        self.current_dialogue = None
        self.current_dialogue_id = None
        

    # ==========================================================
    # Démarrage de texte dynamique (sans JSON)
    # ==========================================================

    def start_text(self, text, font="font0", speed=None):
        """
        Demarre un dialogue a partir d'une chaine de caracteres (ou liste de lignes)
        sans avoir beosin de l'enregistrer dans dialogues.json
        """
        self.active = True
        self.current_dialogue_id = "dynamic_text" # ID temporaire

        if isinstance(text, str):
            lines = [text]
        else:
            lines = text

        # dictionnaire tmporaire
        self.current_dialogue = {
            "font": font,
            "lines": lines
        }
        
        if speed:
            self.current_dialogue["speed"] = speed

        self.current_line_index = 0
        
        font_func = FONT_MAPPING.get(font, FONT_MAPPING["font0"])
        self.current_font = font_func(size=7.5)
        self.text_item.setFont(self.current_font)

        chars_per_second = self.current_dialogue.get("speed", self.base_text_speed)
        self.text_speed_delay = 1.0 / chars_per_second

        if self.box.scene() is None:
            self.scene.addItem(self.box)

        if self.text_item.scene() is None:
            self.scene.addItem(self.text_item)

        self._load_current_line()