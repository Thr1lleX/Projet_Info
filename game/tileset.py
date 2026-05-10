# -*- coding: utf-8 -*-

# --- TILESET --
TILE_TYPES = {
    0: {
        "name": "ground",
        "collision": 0,
        "z": 0
    },
    1: {
        "name": "tree",
        "collision": 1,
        "animated": True,
        "z": 3
    },
    1.5: {
        "name": "tree",
        "collision": 0,
        "animated": True,
        "z": 3
    },
    2: {
        "name": "wall",
        "collision": 1,
        "z": 2
    },
    3: {
        "name": "black",
        "collision": 0,
        "z": 0
    },
    4: {
        "name": "water",
        "collision": 1,
        "animated": True,
        "z": 1
    },
    5: {
        "name": "grass",
        "collision": 0,
        "z": 2
    }
}

"""
assignation collisions 0 intangible, 1 dur
name est le nom du sprite dans le dossier assets
"""