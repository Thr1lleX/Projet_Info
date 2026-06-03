# -*- coding: utf-8 -*-

import json

def load_room(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data