# -*- coding: utf-8 -*-

# --- TILESET --
TILE_TYPES = {
    -1: {
        "name": "empty",
        "collision": 1,
        "z": 0
    },
    0: {
        "name": "ground",
        "collision": 0,
        "z": 0
    },
    0.5: {
        "name": "stones",
        "collision": 0,
        "z": 1
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
    2.1: {
        "name": "breakable_wall",
        "collision": 1,
        "z": 2,
        "breakable": True
    },
    2.2: {
        "name": "broken_wall",
        "collision": 0,
        "z": 0
    },
    2.5: {
        "name": "wall",
        "collision": 0,
        "z": 2
    },
    3: {
        "name": "black",
        "collision": 0,
        "z": 0
    },
    3.5: {
        "name": "black",
        "collision": 1,
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
    },
    6.1: {
        "name": "blue_block_up",
        "collision": 1,
        "z": 2
    },
    6.2: {
        "name": "blue_block_down",
        "collision": 0,
        "z": 0
    },
    7.1: {
        "name": "red_block_up",
        "collision": 1,
        "z": 2
    },
    7.2: {
        "name": "red_block_down",
        "collision": 0,
        "z": 0
    },
    8: {
        "name": "magic_wall",
        "collision": 1,
        "animated": True,
        "z": 2,
        "poofable": True
    },
    9: {
        "name": "bridge",
        "collision": 0,
        "z": 1
    },
    10: {
        "name": "ice",
        "collision": 0,
        "z": 1
    },
    11: {
        "name": "house_fire",
        "collision": 1,
        "animated": True,
        "z": 2
    },
    12: {
        "name": "bookshelves",
        "collision": 1,
        "z": 2
    },
    13: {
        "name": "big_house_entry",
        "collision": 1,
        "animated": False,
        "z": 2
    },
}

"""
assignation collisions 0 intangible, 1 dur
name est le nom du sprite dans le dossier assets
"""