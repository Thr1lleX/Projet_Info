# -*- coding: utf-8 -*-
"""Charge et reference automatiquement toutes les classes d'ennemis du dossier."""

import pkgutil
import importlib
import inspect

from game.enemies.enemy import Enemy
import game.enemies as enemies_pkg


# NOTE, il faut que le nom du fichier matche avec le nom de la classe (1e majuscule pres)



def load_enemy_types():
    """Parcourt le dossier et retourne un dictionnaire des types d'ennemis trouves."""
    enemy_types = {}

    for _, module_name, _ in pkgutil.iter_modules(enemies_pkg.__path__):

        # ignore fichiers spéciaux
        if module_name in ("enemy", "__init__"):
            continue

        module = importlib.import_module(
            f"game.enemies.{module_name}"
        )

        for name, obj in inspect.getmembers(module, inspect.isclass):

            if issubclass(obj, Enemy) and obj is not Enemy:
                enemy_types[module_name.lower()] = obj

    return enemy_types


ENEMY_TYPES = load_enemy_types()