# -*- coding: utf-8 -*-
"""Registre global associant les identifiants d'objets interactifs a leurs classes respectives."""

from game.interactables.savepoint import SavePoint
from game.interactables.npc import NPC
from game.interactables.sign import Sign
from game.interactables.chest import Chest 
from game.interactables.door import LockedDoor 
from game.interactables.door_up import LockedDoorUp
from game.interactables.crystal_switch import CrystalSwitch
from game.interactables.vending_machine import VendingMachine


INTERACTABLE_TYPES = {
    "save_point": SavePoint,
    "npc": NPC,
    "sign" : Sign,
    "chest": Chest,
    "locked_door": LockedDoor,
    "locked_door_up": LockedDoorUp,
    "crystal_switch": CrystalSwitch,
    "vending_machine": VendingMachine
}

