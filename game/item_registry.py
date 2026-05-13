"""
Registre central des items du jeu.

Chaque item est defini une seule fois ici. Le reste du code (inventaire,
drops, sauvegarde, HUD) lit ce catalogue pour connaitre les proprietes
d'un item a partir de son item_id.
"""

ITEM_CATALOG = {
"pomme":{ 
    "name" : "Pomme", 
    "icon_path" : "assets/items/pomme.png",
    "category" : "consumable",
    "stack_max" : 10,
    "effect" : "heal",
    "slot":0
    },
"potion":{ 
    "name" : "Potion de Vitesse", 
    "icon_path" : "assets/items/potion.png",
    "category" : "consumable",
    "stack_max" : 10,
    "effect" : "buff_strength_speed",
    "slot":1
    },
"bombe":{ 
    "name" : "Bombe", 
    "icon_path" : "assets/items/bombe.png",
    "category" : "consumable",
    "stack_max" : 10,
    "effect" : "explode",
    "slot":2
    },
"boomerang":{ 
    "name" : "Boomerang", 
    "icon_path" : "assets/items/boomerang.png",
    "category" : "permanent",
    "stack_max" : 1,
    "effect" : "throw_boomerang",
    "slot":3,
    "required_flag": "has_boomerang"
    },
"fireball":{ 
    "name" : "Magie de Feu", 
    "icon_path" : "assets/items/spear.png",
    "category" : "permanent",
    "stack_max" : 1,
    "effect":    None,
    "slot":4,
    "required_flag": "has_fireball"
    },
"spear":{ 
    "name" : "Lance", 
    "icon_path" : "assets/items/spear.png",
    "category" : "permanent",
    "stack_max" : 1,
    "effect":    "spear",
    "slot":5,
    "required_flag": "has_spear"
    },
"key": { 
        "name" : "Clé", 
        "icon_path" : "assets/items/key.png",
        "category" : "collectible",
        "stack_max" : 99,
        "effect" : None,
        "slot": None
    },
"mana": { 
        "name" : "Mana", 
        "icon_path" : "assets/items/mana.png",
        "category" : "collectible",
        "stack_max" : 10,
        "effect" : None,
        "slot": None
    },
}


def get_item_data(item_id):
    return ITEM_CATALOG.get(item_id)


