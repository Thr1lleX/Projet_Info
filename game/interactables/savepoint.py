# -*- coding: utf-8 -*-

from game.interactables.interactable import Interactable
from game.animspr import load_animation_sequence

from game.config import SCALE, DEBUG


class SavePoint(Interactable):
    def __init__(self, scale=SCALE, x=0, y=0):
        super().__init__(scale)

        self.type = "save_point"

        self.x = x
        self.y = y


        self.collision = 0


        self.hitbox_offset_x = 0
        self.hitbox_offset_y = 0

        self.hitbox_width = self.tile_size
        self.hitbox_height = self.tile_size


        self.frames = load_animation_sequence(
            "assets/savepoint/save_point",
            size=(1, 1)
        )

        self.current_frame = 0
        self.animation_timer = 0

        # durée d'une frame
        self.frame_duration = 0.25

        # sécurité
        if self.frames:
            self.setPixmap(self.frames[0])

        self.update_graphics()


    def update(self, dt):
        """
        animation du savepoint
        """

        if not self.frames:
            return

        self.animation_timer += dt

        if self.animation_timer >= self.frame_duration:

            self.animation_timer = 0

            self.current_frame += 1
            self.current_frame %= len(self.frames)

            self.setPixmap(
                self.frames[self.current_frame]
            )


    def interact(self, scene, player=None):
        """
        Interaction avec le joueur.
        """

        if DEBUG:
            print("Interaction : SavePoint")

        # futur menu de sauvegarde
        if scene.screen_manager:
            scene.screen_manager.open_save_menu()

