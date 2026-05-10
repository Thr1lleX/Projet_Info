from game.sfx import SFXManager
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.attacks.attack_entity import TemporaryAttack
from game.config import TILE_SIZE


class Bomb(TemporaryAttack):
    def __init__(self, source, x, y):
        super().__init__(source, direction="down", damage=2, duration=1.0)
        sprite = QPixmap("assets/items/bombe.png")
        self.setPixmap(
            sprite.scaled(
                int(TILE_SIZE * .75),
                int(TILE_SIZE * .75),
                Qt.IgnoreAspectRatio,
                Qt.FastTransformation
            )
        )
        self.x = x
        self.y = y
        self.setPos(self.x, self.y)
        self.fuse_timer = 1.0
        self.exploded = False
        self.blast_radius = TILE_SIZE
        self.hurt_player = True
        self.frames = []
        self.anim_speed = 999

    def update(self, dt, scene):
        self.fuse_timer -= dt
        if self.fuse_timer <= 0 and not self.exploded:
            self._explode(scene)

    def update_position(self):
        pass

    def _explode(self, scene):
        """Inflige des degats dans le rayon puis disparait."""
        self.exploded = True
        cx = self.x + TILE_SIZE / 2
        cy = self.y + TILE_SIZE / 2

        # degats aux ennemis
        for enemy in scene.enemies[:]:
            ex, ey, ew, eh = enemy.get_hitbox()
            ecx = ex + ew / 2
            ecy = ey + eh / 2
            dist = ((cx - ecx) ** 2 + (cy - ecy) ** 2) ** 0.5
            if dist <= self.blast_radius:
                enemy.take_damage(scene, self.damage, self.source)

        # degats au joueur (optionnel)
        if self.hurt_player:
            px, py, pw, ph = scene.player.get_hitbox()
            pcx = px + pw / 2
            pcy = py + ph / 2
            dist = ((cx - pcx) ** 2 + (cy - pcy) ** 2) ** 0.5
            if dist <= self.blast_radius:
                scene.player.take_damage(scene, self.damage, self)

        # TODO: vfx explosion ici
        # TODO: sfx explosion ici
        self.die()

    def die(self):
        """Retire la bombe de la scene."""
        if self.scene():
            self.scene().removeItem(self)
