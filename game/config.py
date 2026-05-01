# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt

# --- CONFIG 
SCALE = 4  # x1 -> 1 tile = 16x16 pixels
BASE_TILE_SIZE = 16

TILE_SIZE = BASE_TILE_SIZE * SCALE

GRID_WIDTH = 16
GRID_HEIGHT = 11
HUD_HEIGHT = 2  # en tiles

BASE_SPEED_pxl = 90  # en base pixels / seconds
BASE_SPEED = BASE_SPEED_pxl * SCALE

FPS = 60
interval = int(1000 / FPS)

DEBUG = False


DURATION_FADE_OUT_ROOM = 0.3
DURATION_FADE_IN_ROOM = 0.35 #aussi duree de freeze du jeu lorsque changement de musique

# Touches

KEYS = {"UP": Qt.Key_Up,
        "LEFT" : Qt.Key_Left,
        "RIGHT" : Qt.Key_Right,
        "DOWN" : Qt.Key_Down,
        "SPRINT" : Qt.Key_Shift,
        "CROUCH" : Qt.Key_Control,
        "LEAVE" : Qt.Key_Escape,
        "INTERACT" : Qt.Key_Q,
        "ATTACK" : Qt.Key_W,
        "ITEM" : Qt.Key_X,
        "SHOUTS" : Qt.Key_M
        }


PAUSE_VOLUME_FACTOR = 0.3   # facteur de volume musique pendant la pause

CRT_OVERLAY = True

# music_volume = 0.6
# sfx_volume = 1.0
# ui_volume = 0.8

# --- Z-ORDER (priorite de rendu) ---
Z_HUD    = 1000
Z_CRT    = 9999
Z_SCREEN = 10000   # ecrans superposables (titre, game over, parametres)

# --- HUD ---
HUD_ITEM_SLOTS       = 6
HUD_HEART_FULL_PATH  = "assets/hud/heart_full.png"
HUD_HEART_EMPTY_PATH = "assets/hud/heart_empty.png"
HUD_ITEM_SLOT_PATH   = "assets/hud/item_slot.png"

# --- TITRE ET MENUS ---
# Taille attendue pour title_bg.png : 1024 x 832 px (GRID_WIDTH*TILE_SIZE x (GRID_HEIGHT+HUD_HEIGHT)*TILE_SIZE)
TITLE_BG_PATH = "assets/title_bg.png"
GAME_TITLE    = "Vivit'lair"