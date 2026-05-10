"""
Registre central des items du jeu.

Chaque item est defini une seule fois ici. Le reste du code (inventaire,
drops, sauvegarde, HUD) lit ce catalogue pour connaitre les proprietes
d'un item a partir de son item_id.
"""

ITEM_CATALOG = {

"sword" : { 
    "name" : "sword", 
    "icon_path" : "assets/items/sword.png",
    "category" : "weapon",
    "stack_max" : 1,
    "effect":    None} ,    
"spear":{ 
    "name" : "spear", 
    "icon_path" : "assets/items/spear.png",
    "category" : "weapon",
    "stack_max" : 1,
    "effect":    None},
"boomerang":{ 
    "name" : "boomerang", 
    "icon_path" : "assets/items/boomerang.png",
    "category" : "permanent",
    "stack_max" : 1,
    "effect" : "throw_boomerang"},
"pomme":{ 
    "name" : "pomme", 
    "icon_path" : "assets/items/pomme.png",
    "category" : "consumable",
    "stack_max" : 10,
    "effect" : "heal"},
"potion":{ 
    "name" : "potion", 
    "icon_path" : "assets/items/potion.png",
    "category" : "consumable",
    "stack_max" : 10,
    "effect" : "buff_strength_speed"},
"bombe":{ 
    "name" : "bombe", 
    "icon_path" : "assets/items/bombe.png",
    "category" : "consumable",
    "stack_max" : 10,
    "effect" : "explode"}
}

LOOT_TABLE = [
    ("pomme",  0.50),   # 50% de chance
    ("potion", 0.50),
    ("bombe",  0.50),
]


def get_item_data(item_id):
    return ITEM_CATALOG.get(item_id)


