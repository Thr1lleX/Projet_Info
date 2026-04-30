# -*- coding: utf-8 -*-

# --- TILESET --
TILE_TYPES = {
    0: {
        "name": "ground",
        "collision": 0
    },
    1: {
        "name": "tree",
        "collision": 1,
        "animated": True
    },
    2: {
        "name": "wall",
        "collision": 1
    },
    3: {
        "name": "black",
        "collision": 0
    },
    4: {
        "name": "water",
        "collision": 1,
        "animated": True
    }
}

"""
assignation collisions 0 intangible, 1 dur
name est le nom du sprite dans le dossier assets
"""