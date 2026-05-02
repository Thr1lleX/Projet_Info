# -*- coding: utf-8 -*-
"""
Gestionnaire de parametres persistants (SettingsManager).

Charge et sauvegarde les preferences du joueur dans settings.json.
Applique les changements aux objets du jeu (scene, fenetre).

Valeurs par defaut :
  music_volume    = 0.6   (0.0 - 1.0)
  sfx_volume      = 1.0   (0.0 - 1.0)
  crt_overlay     = True
  debug_hitboxes  = False
  tile_anim_speed = 0.5   (duree en secondes d'une frame d'animation tile)

Pour ajouter un nouveau parametre :
  1. Ajouter la cle et sa valeur par defaut dans _DEFAULTS.
  2. Ajouter l'attribut correspondant dans __init__ et les methodes load/save.
  3. Ajouter la logique d'application dans apply_to_scene()
"""

import json
import os

_SETTINGS_PATH = "settings.json"

_DEFAULTS = {
    "music_volume":    1,
    "sfx_volume":      0.95,
    "crt_overlay":     True,
    "debug_hitboxes":  False,
    "tile_anim_speed": 0.5,
}


class SettingsManager:
    """Lit, ecrit et applique les preferences de jeu."""

    def __init__(self):
        self.music_volume    = _DEFAULTS["music_volume"]
        self.sfx_volume      = _DEFAULTS["sfx_volume"]
        self.crt_overlay     = _DEFAULTS["crt_overlay"]
        self.debug_hitboxes  = _DEFAULTS["debug_hitboxes"]
        self.tile_anim_speed = _DEFAULTS["tile_anim_speed"]

        self.load()

    # ------------------------------------------------------------------
    # persistance
    # ------------------------------------------------------------------

    def load(self):
        """Charge settings.json si present ; ignore les cles inconnues."""
        if not os.path.exists(_SETTINGS_PATH):
            return
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, default in _DEFAULTS.items():
                raw = data.get(key, default)
                if isinstance(default, bool):
                    setattr(self, key, bool(raw))
                elif isinstance(default, float):
                    val = float(raw)
                    if key.endswith("volume"):
                        val = max(0.0, min(1.0, val))
                    setattr(self, key, val)
                else:
                    setattr(self, key, raw)
        except (json.JSONDecodeError, ValueError, TypeError, OSError):
            pass  # fichier corrompu -> on garde les defaults

    def save(self):
        """Ecrit les parametres actuels dans settings.json."""
        data = {
            "music_volume":    self.music_volume,
            "sfx_volume":      self.sfx_volume,
            "crt_overlay":     self.crt_overlay,
            "debug_hitboxes":  self.debug_hitboxes,
            "tile_anim_speed": self.tile_anim_speed,
        }
        try:
            with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # application
    # ------------------------------------------------------------------

    def apply_to_scene(self, scene):
        """Applique les parametres audio et visuels a la scene active."""
        if hasattr(scene, 'music_manager'):
            scene.music_manager.set_volume(self.music_volume)
        if hasattr(scene, 'sfx_manager'):
            scene.sfx_manager.set_volume(self.sfx_volume)
        if hasattr(scene, 'frame_duree'):
            scene.frame_duree = self.tile_anim_speed
        if hasattr(scene, 'crt_overlay'):
            scene.crt_overlay.setVisible(self.crt_overlay)


