# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan
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


from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from game.save_manager import SaveManager
from game.music import MusicManager
from game.settings import settings


class ScreenManager:
    """Chef d'orchestre de la navigation entre les ecrans."""

    STATE_TITLE     = "title"
    STATE_CONTROLS  = "controls"
    STATE_GAME      = "game"
    STATE_PAUSED    = "paused"
    STATE_INVENTORY = "inventory"
    STATE_GAME_OVER = "game_over"
    STATE_SETTINGS  = "settings"
    STATE_SAVE_MENU = "save_menu"

    def __init__(self, window):
        self.window         = window
        self._scene         = None
        self._screens       = {}
        self._active_screen = None
        self.state          = None
        self._prev_state    = None      # etat precedent (retour depuis parametres)

        # injectes depuis main.py
        self.settings  = None   # SettingsManager
        self.inventory = None   # Inventory
        
        self.music_manager = MusicManager()

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
            if self._scene and self._scene.dialogue_manager.active:
                # on ne fait rien, on laisse la touche passer au jeu mais empeche ouverture
                if key == settings.keys["PAUSE"] or key == settings.keys["INVENTORY"]:
                    return True
            if key == settings.keys["PAUSE"]:
                self.open_pause()
                return True
            if key == settings.keys["INVENTORY"]:
                self.open_inventory()
                return True

        return False

    def route_key_release(self, key):
        """Transmet le key_release a l'ecran actif (pour l'etat 'pressed' des boutons)."""
        if self._active_screen is not None:
            self._active_screen.key_release(key)
            return True
        return False

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
    
    def go_to_title(self):
        """
        Retourne a l'ecran titre.
        Cree une scene fraiche (en pause) et affiche le menu principal.
        """
        self.hide_current_screen()
        self._create_fresh_scene()       # game_paused = True par defaut dans GameScene
        
        if self.music_manager.current_music != "mus_title":
            self.music_manager.play("mus_title")
        
        self.show_screen("title")
        self.state = self.STATE_TITLE

    def go_to_settings(self):
        """Affiche l'ecran des parametres en memorisant l'etat precedent."""
        # verifie si on vient de l'ecran titre pour autoriser le re-scale
        allow_rescale = (self.state == self.STATE_TITLE)
        
        settings_scr = self._screens.get("settings")
        if settings_scr:
            settings_scr.set_rescale_allowed(allow_rescale)
        
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
        """Met le jeu en pause et joue la musique de pause avec le sfx (joue musique 600ms apres)."""
        if self.scene is None:
            return
        if hasattr(self.scene, 'player'):
            self.scene.player.stop_movement()
        
        self.scene.game_paused = True
        if hasattr(self.scene, 'music_manager'):
            self.music_manager.stop()
        if hasattr(self._scene, 'sfx_manager'):
            self.scene.sfx_manager.stop_all_except()
            self.scene.sfx_manager.play("snd_sys_pause")
        # fonction labma pour check si on est toujours en pause avant de jouer (empeche spam)
        QTimer.singleShot(200, lambda: self._play_music_if_state("mus_pause", self.STATE_PAUSED))
            
        self.show_screen("pause")
        self.state = self.STATE_PAUSED

    def resume_game(self):
        """Reprend le jeu et relance la musique de la room avec fade-in."""
        self.hide_current_screen()
        if self._scene is not None:
            if hasattr(self._scene, 'sfx_manager'):
                self._scene.sfx_manager.play("snd_sys_resume")

            self._scene.start_room_music()
            self._scene.game_paused = False
            
        self.state = self.STATE_GAME

    # ------------------------------------------------------------------
    # inventaire
    # ------------------------------------------------------------------
    def open_inventory(self):
        """Gele le jeu et joue la musique d'inventaire."""
        if self._scene is None:
            return
        
        # supprime les touches fantome!!!
        if hasattr(self._scene, 'player'):
            self._scene.player.stop_movement()
            
        self._scene.game_paused = True
        if hasattr(self._scene, 'music_manager'):
            self.music_manager.stop()
        if hasattr(self._scene, 'sfx_manager'):
            self._scene.sfx_manager.play("snd_sys_item")
        QTimer.singleShot(200, lambda: self._play_music_if_state("mus_inventory", self.STATE_INVENTORY))
            
        self.show_screen("inventory")
        self.state = self.STATE_INVENTORY

    def close_inventory(self):
        """Ferme l'inventaire et reprend la musique du jeu."""
        self.hide_current_screen()
        if self._scene is not None:
            if hasattr(self._scene, 'sfx_manager'):
                self._scene.sfx_manager.play("snd_sys_resume")
            # Relance la musique de la salle (avec fade_in configuré dans le JSON)
            self._scene.start_room_music()
            self._scene.game_paused = False
            
        self.state = self.STATE_GAME

    def toggle_inventory(self):
        """Ouvre ou ferme l'inventaire selon l'etat actuel."""
        if self.state == self.STATE_INVENTORY:
            self.close_inventory()
        elif self.state == self.STATE_GAME:
            self.open_inventory()
            
    def _play_music_if_state(self, music_name, target_state):
        """Joue la musique uniquement si le manager est encore dans l'etat voulu."""
        if self.state == target_state and self._scene and hasattr(self._scene, 'music_manager'):
            self.music_manager.play(music_name)

    def load_game(self, slot=1):
    
        self.hide_current_screen()
    
        scene = self._create_fresh_scene()
    
        scene.load_save(slot)
    
        scene.game_paused = False
        scene.start_room_music()
    
        self.state = self.STATE_GAME
    
        if self.settings is not None:
            self.settings.apply_to_scene(scene)
        
    
    def start_new_game(self):
        """
        initialise la session mais affiche l'ecran de controles d'abord
        """
    
        self.hide_current_screen()
    
        scene = self._create_fresh_scene()
    
        # save temporaire non liée à un slot
        scene.current_save = SaveManager(slot=None)
    
        scene.load_current_save()
    
        if self.settings is not None:
            self.settings.apply_to_scene(scene)
    
        if self.inventory is not None:
            self.inventory.reset()
            # # items de depart (hors debug)
            # self.inventory.add_item("bombe", 5)
            # self.inventory.add_item("pomme", 5)
            # self.inventory.equip_item("bombe")
        if hasattr(self, 'music_manager'):
            self.music_manager.stop()
            
        controls_scr = self._screens.get(self.STATE_CONTROLS)
        if hasattr(controls_scr, 'reset_build'):
            controls_scr.reset_build()
            
        self.show_screen("controls")
        self.state = self.STATE_CONTROLS

            
    def finalize_new_game(self, wipe_item):
        """
        affiche la scene lors d'une nouvelle partie
        """
        
        if self._scene is not None:
            self._scene.game_paused = False
            self._scene.start_room_music()
            
            # detacher overlay de l'ecran de controle pour le mettre a la racine 
            # et gerer separement pour fondu d'ouverture
            if self._active_screen and wipe_item in self._active_screen._items:
                self._active_screen._items.remove(wipe_item)
            
            self._scene.addItem(wipe_item)
        
        self.state = self.STATE_GAME
        self.hide_current_screen() 
        
        # lancer fondu overlay
        self.final_fade = QPropertyAnimation(wipe_item, b"opacity")
        self.final_fade.setDuration(500) # 0.2s
        self.final_fade.setStartValue(1.0)
        self.final_fade.setEndValue(0.0)
        
        # retire de la scene
        self.final_fade.finished.connect(lambda: self._scene.removeItem(wipe_item) if self._scene else None)
        self.final_fade.start()
        
    # sauvegardes
    
    def open_save_menu(self):
        if self._scene is None:
            return
    
        if hasattr(self._scene, "player"):
            self._scene.player.stop_movement()
        self._scene.game_paused = True
        if hasattr(self._scene, 'sfx_manager'):
            self._scene.sfx_manager.play("snd_sys_save")
        # on joue un peu apres sfx
        QTimer.singleShot(200,lambda: self._play_music_if_state("mus_save",self.STATE_SAVE_MENU))
        
        self.show_screen("save_menu")
        self.state = self.STATE_SAVE_MENU
        
        
    def close_save_menu(self):
    
        self.hide_current_screen()
    
        if self._scene is not None:

            self._scene.start_room_music()
            self._scene.game_paused = False
    
        self.state = self.STATE_GAME
        
    # ------------------------------------------------------------------
    # Application des parametres
    # ------------------------------------------------------------------

    def apply_crt(self):
        if self._scene and hasattr(self._scene, 'update_crt'):
            from game.settings import settings
            self._scene.update_crt(settings.crt_overlay)

    
    def rebuild_display(self):
        """
        Reconstruit tout l'affichage lors d'un changement de résolution (SCALE).
        """
        # cacher ecran actuel
        self.hide_current_screen()
        
        # vider tous les ecran pour re forcer _build
        for screen in self._screens.values():
            if hasattr(screen, 'reset_build'):
                screen.reset_build()
                
        # change taille fenetre
        if hasattr(self.window, 'update_window_size'):
            self.window.update_window_size()
            
        # re-cree scene vierge
        self._create_fresh_scene()
        
        # re-affiche ecran de parametres
        self.show_screen("settings")
