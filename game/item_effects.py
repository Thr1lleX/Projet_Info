# auteur : essentiellement Ryan
"""Definit les effets declenches lors de l'utilisation d'objets ou d'armes."""
from game.settings import settings
from game.item_registry import get_item_data
from game.attacks.bomb import Bomb
from game.attacks.boomerang import Boomerang

def use_item(player, scene):
    """Execute l'effet de l'objet equipe et le consomme si necessaire."""
    inventory = scene.screen_manager.inventory
    item_id = inventory._equipped_item_id
    if item_id is None:
        return False
    data = get_item_data(item_id)
    if data is None:
        return False

    effect = data["effect"]
    category = data["category"]

    # verifier qu'on a le stock (consommables uniquement)
    if category == "consumable":
        if not inventory.has_item(item_id):
            return False

    # executer l'effet
    effect_fn = _EFFECTS.get(effect)
    if effect_fn is None:
        return False

    success = effect_fn(player, scene)

    # consommer apres usage reussi
    if success and category == "consumable":
        inventory.consume_one(item_id)

    return success


# fonctions effets
def _effect_heal(player, scene):
    """Pomme : regenere 1 coeur."""
    if player.pv_main >= player._pv_max:
        return False   # deja plein, ne pas gaspiller
    player.pv_main = min(player.pv_main + 1, player._pv_max)
    scene.sfx_manager.play("snd_pomme")
    return True


def _effect_buff(player, scene):
    """Potion : +20% degats et vitesse pendant 15s."""
    player.apply_buff()
    scene.sfx_manager.play("snd_potion")
    return True


def _effect_explode(player, scene):
    """Bombe : pose une bombe 1 tile devant le joueur."""

    offsets = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    dx, dy = offsets[player.direction]
    bomb_x = player.x + dx * settings.tile_size
    bomb_y = player.y + dy * settings.tile_size

    bomb = Bomb(player, bomb_x, bomb_y)
    scene.addItem(bomb)
    scene.sfx_manager.play("snd_placebomb")
    player.projectiles.append(bomb)

    return True

def _effect_boomerang(player, scene):
    """Boomerang : lance le boomerang (code existant)."""
    player.throw_boomerang(scene)
    return True

def _effect_spear(player, scene):
    """lance : utilise la lance (code existant)."""
    player.spear(scene)
    return True

def _effect_fireball(player, scene):
    """Magie de Feu : lance une boule de feu en ligne droite en consommant 1 de Mana."""
    inventory = scene.screen_manager.inventory
    
    if not inventory.count_item("mana") > 0:
        scene.sfx_manager.play("snd_false")
        return False
    
    inventory.consume_one("mana")
    
    player.shoot_fireball(scene)
    scene.sfx_manager.play("snd_fireball") 
    
    return True



# ------------------------------------------------------------------
# table de dispatch
# ------------------------------------------------------------------

_EFFECTS = {
    "heal":                _effect_heal,
    "buff_strength_speed": _effect_buff,
    "explode":             _effect_explode,
    "throw_boomerang":     _effect_boomerang,
    "shoot_fireball":      _effect_fireball,
    "spear": _effect_spear
}
