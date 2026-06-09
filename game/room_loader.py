# -*- coding: utf-8 -*-

import json

def load_room(path):
    """Lit et retourne le dictionnaire JSON d'une salle."""
    with open(path, "r") as f:
        data = json.load(f)
    return data