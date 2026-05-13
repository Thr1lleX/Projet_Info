# -*- coding: utf-8 -*-

from game.interactables.savepoint import SavePoint
from game.interactables.npc import NPC
from game.interactables.sign import Sign
from game.interactables.chest import Chest 
from game.interactables.door import LockedDoor 


INTERACTABLE_TYPES = {
    "save_point": SavePoint,
    "npc": NPC,
    "sign" : Sign,
    "chest": Chest,
    "locked_door": LockedDoor
}

