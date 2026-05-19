# -*- coding: utf-8 -*-

from game.attacks.sword_slash import SwordSlash

class SwordSlashTungsten(SwordSlash):
    def __init__(self, player, direction):
        
        super().__init__(player, direction,spr_path = "player/attack/sword_tungsten")
        
        self.damage = self.source.damage * 2