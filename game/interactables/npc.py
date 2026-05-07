# -*- coding: utf-8 -*-

from game.interactables.interactable import Interactable
class NPC(Interactable):
    pass

    def interact(self, scene):
        scene.dialogue_manager.start_dialogue(...)