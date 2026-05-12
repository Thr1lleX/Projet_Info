# -*- coding: utf-8 -*-

from game.interactables.savepoint import SavePoint
from game.interactables.npc import NPC
from game.interactables.sign import Sign
from game.interactables.chest import Chest 

INTERACTABLE_TYPES = {
    "save_point": SavePoint,
    "npc": NPC,
    "sign" : Sign,
    "chest": Chest
}

