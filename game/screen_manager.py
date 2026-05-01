# -*- coding: utf-8 -*-
"""
Gestionnaire d'ecrans (ScreenManager).

Role :
  - Connaitre l'etat global de l'application (titre / jeu / pause / inventaire /
    game over / parametres).
  - Afficher ou masquer les ecrans (BaseScreen) sur la scene courante.
  - Router les evenements clavier et souris vers l'ecran actif.
  - Creer une nouvelle GameScene propre lors d'un reset ou d'un retour au menu.
  - Gerer la pause (freeze jeu + baisse du volume musique).
  - Gerer l'inventaire (freeze jeu + affichage overlay).

Attributs publics injectes depuis main.py :
  sm.settings  = SettingsManager
  sm.inventory = Inventory

Utilisation typique (main.py) :
    sm = ScreenManager(window)
    sm.settings  = SettingsManager()
    sm.inventory = Inventory(30)
    sm.register_screen("title",     TitleScreen(sm))
    sm.register_screen("game_over", GameOverScreen(sm))
    sm.register_screen("settings",  SettingsScreen(sm))
    sm.register_screen("pause",     PauseScreen(sm))
    sm.register_screen("inventory", InventoryScreen(sm))
    sm.go_to_title()

Pour ajouter un nouvel ecran :
    1. Creer une sous-classe de BaseScreen.
    2. sm.register_screen("mon_ecran", MonEcran(sm)).
    3. Appeler sm.show_screen("mon_ecran") au moment voulu.
"""

from PyQt5.QtCore import Qt

from game.config import PAUSE_VOLUME_FACTOR


class ScreenManager:
    """Chef d'orchestre de la navigation entre les ecrans."""

    STATE_TITLE     = "title"
    STATE_GAME      = "game"
    STATE_PAUSED    = "paused"
    STATE_INVENTORY = "inventory"
    STATE_GAME_OVER = "game_over"
    STATE_SETTINGS  = "settings"

    def __init__(self, window):
        self.window         = window
        self._scene         = None
        self._screens       = {}
        self._active_screen = None
        self.state          = None
        self._prev_state    = None      # etat precedent (retour depuis parametres)
        self._pre_pause_volume = 1.0   # volume avant pause (restaure au resume)

        # injectes depuis main.py
        self.settings  = None   # SettingsManager
        self.inventory = None   # Inventory

    # ------------------------------------------------------------------
    # gestion de la scene
    # ------------------------------------------------------------------

    @property
    def scene(self):
        return self._scene

    def set_scene(self, scene):
        """Definit la scene active et y attache une reference vers ce manager."""
        self._scene = scene
        scene.screen_manager = self

    def _create_fresh_scene(self):
        """
        Arrete proprement l'ancienne scene et en cree une nouvelle.
        Retourne la nouvelle GameScene (deja installee dans la fenetre).
        """
        from game.scene import GameScene   # import tardif pour eviter les imports circulaires

        old = self._scene
        if old is not None:
            if hasattr(old, 'timer'):
                old.timer.stop()
            if hasattr(old, 'music_manager'):
                old.music_manager.stop()

        new_scene = GameScene(screen_manager=self)
        self.set_scene(new_scene)
        self.window.setScene(new_scene)
        return new_scene

    # ------------------------------------------------------------------
    # gestion des ecrans
    # ------------------------------------------------------------------

    def register_screen(self, name, screen):
        """Enregistre un ecran sous un nom cle."""
        self._screens[name] = screen

    def show_screen(self, name):
        """
        Masque l'ecran actif (s'il y en a un) et affiche le nouvel ecran.
        Les items de l'ancien ecran sont retires via item.scene() (sur-place),
        ce qui fonctionne meme si la scene a ete remplacee.
        """
        if self._active_screen is not None:
            self._active_screen.hide()
        self._active_screen = self._screens[name]
        self._active_screen.show(self._scene)

    def hide_current_screen(self):
        """Masque l'ecran actif sans en afficher un autre."""
        if self._active_screen is not None:
            self._active_screen.hide()
            self._active_screen = None

    # ------------------------------------------------------------------
    # routage des evenements
    # ------------------------------------------------------------------

    def route_key_press(self, key):
        """
        Transmet la touche a l'ecran actif s'il y en a un.
        Sinon, intercepte Echap (→ pause) et Tab (→ inventaire) pendant le jeu.
        Retourne True si l'evenement est consomme (ne doit pas atteindre le jeu).
        """
        if self._active_screen is not None:
            self._active_screen.key_press(key)
            return True

        if self.state == self.STATE_GAME:
            if key == Qt.Key_Escape:
                self.open_pause()
                return True
            if key == Qt.Key_Tab:
                self.open_inventory()
                return True

        return False

    def route_key_release(self, key):   # noqa: ARG002
        """Absorbe les key_release quand un ecran est actif."""
        return self._active_screen is not None

    def route_mouse_press(self, scene_pos):
        """
        Transmet le clic (QPointF en coordonnees scene) a l'ecran actif.
        Retourne True si consomme.
        """
        if self._active_screen is not None:
            self._active_screen.mouse_press(scene_pos)
            return True
        return False

    # ------------------------------------------------------------------
    # transitions entre etats principaux
    # ------------------------------------------------------------------

    def start_new_game(self):
        """
        Demarre une nouvelle partie depuis zero.
        Retire l'ecran actif, cree une scene fraiche et lance le jeu.
        Applique les parametres (settings) et reinitialise l'inventaire.
        """
        self.hide_current_screen()
        scene = self._create_fresh_scene()
        scene.game_paused = False
        scene.start_room_music()
        self.state = self.STATE_GAME

        if self.settings is not None:
            self.settings.apply_to_scene(scene)
        if self.inventory is not None:
            self.inventory.reset()

    def go_to_title(self):
        """
        Retourne a l'ecran titre.
        Cree une scene fraiche (en pause) et affiche le menu principal.
        """
        self.hide_current_screen()
        self._create_fresh_scene()       # game_paused = True par defaut dans GameScene
        self.show_screen("title")
        self.state = self.STATE_TITLE

    def go_to_settings(self):
        """Affiche l'ecran des parametres en memorisant l'etat precedent."""
        self._prev_state = self.state
        self.show_screen("settings")
        self.state = self.STATE_SETTINGS

    def back_from_settings(self):
        """
        Retourne a l'ecran precedent depuis les parametres.
          - Depuis le titre   : reaffiche le titre.
          - Depuis le jeu     : reprend le jeu.
          - Depuis la pause   : reaffiche le menu pause.
        """
        prev = self._prev_state or self.STATE_TITLE
        if prev == self.STATE_TITLE:
            self.show_screen("title")
            self.state = self.STATE_TITLE
        elif prev == self.STATE_GAME:
            self.hide_current_screen()
            self.state = self.STATE_GAME
        elif prev == self.STATE_PAUSED:
            self.show_screen("pause")
            self.state = self.STATE_PAUSED
        else:
            self.show_screen("title")
            self.state = self.STATE_TITLE

    def on_game_over(self):
        """
        Appele par player.die() quand le joueur meurt.
        Stoppe le gameplay via scene.game_over() et affiche l'ecran de fin.
        """
        self.state = self.STATE_GAME_OVER
        if self._scene is not None:
            self._scene.game_over()
        self.show_screen("game_over")

    def quit_game(self):
        """Ferme l'application proprement."""
        if self._scene is not None and hasattr(self._scene, 'timer'):
            self._scene.timer.stop()
        self.window.quitter_jeu()

    # ------------------------------------------------------------------
    # pause
    # ------------------------------------------------------------------

    def open_pause(self):
        """
        Met le jeu en pause :
          - gele la boucle de jeu (game_paused = True),
          - baisse le volume de la musique,
          - affiche le menu pause.
        """
        if self._scene is None:
            return
        self._scene.game_paused = True
        if hasattr(self._scene, 'music_manager'):
            mm = self._scene.music_manager
            self._pre_pause_volume = mm.target_volume
            mm.set_volume(self._pre_pause_volume * PAUSE_VOLUME_FACTOR)
        self.show_screen("pause")
        self.state = self.STATE_PAUSED

    def resume_game(self):
        """
        Reprend le jeu depuis la pause :
          - restaure le volume musique,
          - retire le menu pause,
          - degele la boucle de jeu.
        """
        self.hide_current_screen()
        if self._scene is not None:
            if hasattr(self._scene, 'music_manager'):
                self._scene.music_manager.set_volume(self._pre_pause_volume)
            self._scene.game_paused = False
        self.state = self.STATE_GAME

    # ------------------------------------------------------------------
    # inventaire
    # ------------------------------------------------------------------

    def open_inventory(self):
        """Gele le jeu et affiche l'ecran d'inventaire."""
        if self._scene is None:
            return
        self._scene.game_paused = True
        self.show_screen("inventory")
        self.state = self.STATE_INVENTORY

    def close_inventory(self):
        """Ferme l'inventaire et reprend le jeu."""
        self.hide_current_screen()
        if self._scene is not None:
            self._scene.game_paused = False
        self.state = self.STATE_GAME

    def toggle_inventory(self):
        """Ouvre ou ferme l'inventaire selon l'etat actuel."""
        if self.state == self.STATE_INVENTORY:
            self.close_inventory()
        elif self.state == self.STATE_GAME:
            self.open_inventory()
