# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt
from game.config import DEBUG
from game.settings import settings

def load_animation_sequence(folder_path, size, frame_count=None):
    """
    charge une suite d'images et scale a TILE_SIZE
    
    Parameters
    -----
    folder_path : str
        "assets/player/attack/sword" et le code cherchera pour les sword1.png, sword2.png
    frame_count : int
    size : int*int
        taille en tiles
    """
    # on recupere les tailles en pixels scaled
    width = size[0]*settings.tile_size
    height = size[1]*settings.tile_size
    frames = []
    
    i=1
    while True:
        if frame_count is not None and i > frame_count:
            break
        file_path = folder_path+f"{i}.png"
        pixmap = QPixmap(file_path)
        
        if pixmap.isNull():
            #si on est en mode auto (None), indicateur poyr s'arreter
            if frame_count is None:
                break
            
            # mode normal, si on ne charge pas, alors erreur
            else:
            
                if DEBUG:
                    print(f" Alerte : Frame {i} manquante dans {folder_path}")
                    i += 1
                continue
            
        scaled_frame = pixmap.scaled(
            int(width), 
            int(height), 
            transformMode=Qt.FastTransformation
        )
        frames.append(scaled_frame)
        i += 1
        
    if not frames:
        raise FileNotFoundError(f"La sequence d'image de {folder_path} n'existe pas.")
    return frames


def generate_directional_animations(base_frames, pos, size):
    """
    En gros quand on tourne un sprite, celui ci va provenir d'une entite (en general joueur)
    et le sprite va etre defini sur une matrice mxn de tiles avec le joueur en ij
    donc quand on va faire la rotation, il faut tourner avec le joueur au centre, 
    et decaler l'anim de x tiles selon la direction
    
    On suppose que tous les sprites sont faits avec direction vers haut
    
    format de placement en commencant a compter par 0 en haut a gauche = 0,0)
        

    Parameters
    ----------
    base_frames : list
        liste des frames scaled, a utiliser avec load_animation_sequence.
    pos : int*int
        position en tiles de mon joueur par rapport aux sprites, commence par 0.
    size : int*int
        taille en tiles de mes sprites (tous de la meme taille.

    Returns dict[str, dict[str, Any]]
    {
    "up": {
        "frames": [...],
        "offset": (x, y) # en pixels!
    },
    ...
    }
    """
    pos_x = pos[0]
    pos_y = pos[1]
    
    taille_x = size[0]
    taille_y = size[1]
    
    
    directions = {
        "up": 0,
        "left": -90,
        "right":90,
        "down": 180
    }
    
    result = {}
    
    if base_frames : # on skip si vide, ca optimise un peu je pense
        for dir_name, angle in directions.items():
            # formule d'offset de centre - difference pos au coin gauche apres rot
            if dir_name == "up":
                offset_x = -pos_x
                offset_y = -pos_y
                
            elif dir_name == "left":
                offset_x = -pos_y
                offset_y = pos_x - (taille_x-1)
                
            elif dir_name == "right":
                offset_x = pos_y - (taille_y-1)
                offset_y = -pos_x
                
            else:
                offset_x = pos_x - (taille_x-1)
                offset_y = pos_y - (taille_y-1)
                
            # conversion en pxl
            offset_x_pxl = offset_x * settings.tile_size
            offset_y_pxl = offset_y * settings.tile_size
            
            # rotations
            transform = QTransform()
            transform.rotate(angle)
    
            # stockage
            rotated_frames = []
            for frame in base_frames:
                if angle == 0:
                    rotated_frames.append(frame)
                else:
                    rotated_pixmap = frame.transformed(transform, Qt.FastTransformation)
                    rotated_frames.append(rotated_pixmap)
    
            result[dir_name] = {
                "frames": rotated_frames,
                "offset": (offset_x_pxl, offset_y_pxl)
            }
        return result
