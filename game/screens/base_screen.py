# -*- coding: utf-8 -*-
"""
Classe de base pour tous les ecrans superposables (titre, game over, parametres...).

Principe :
  - Chaque ecran est une collection de QGraphicsItems.
  - Les items sont crees une seule fois dans _build() au premier show().
  - show(scene) ajoute les items a la scene ; hide() les retire.
  - Les evenements clavier et souris sont recouverts dans les sous-classes.

Pour creer un nouvel ecran :
  1. Heriter de BaseScreen
  2. Implementer _build() en remplissant self._items
  3. Surcharger key_press() et/ou mouse_press() si necessaire
"""

from game.config import (
    GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, TILE_SIZE, SCALE,
    Z_SCREEN, KEYS,
)

_SCENE_W = GRID_WIDTH * TILE_SIZE
_SCENE_H = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

class BaseScreen:
    """
    Classe abstraite dont heritent tous les ecrans.
    Ne pas instancier directement.
    """
  # --- Parametres de layout (surchageables par les sous-classes) ---
    _menu_start_ratio = 0.50   # position Y du 1er bouton (fraction de la hauteur scene)
    _menu_spacing     = 4      # ecart entre boutons en pixels base (multiplie par SCALE)

    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self._items    = []
        self._visible  = False
        self._built    = False

        # --- menu (rempli par les sous-classes) ---
        self._menu       = []
        self._selected   = 0
        self._btns       = []      # liste de SpriteButton
        self._is_pressed = False
    # ------------------------------------------------------------------
    # cycle de vie
    # ------------------------------------------------------------------

    def show(self, scene):
        """Affiche l'ecran : construit les items si necessaire, puis les ajoute a la scene."""
        if not self._built:
            self._build()
            self._built = True
        for item in self._items:
            if item.scene() is None:
                scene.addItem(item)
        self._visible = True

    def hide(self):
        """Retire les items de leur scene courante (fonctionne meme apres un swap de scene)."""
        for item in self._items:
            current = item.scene()
            if current is not None:
                current.removeItem(item)
        self._visible = False

    def _build(self):
        """
        Cree les QGraphicsItems de l'ecran et les ajoute dans self._items.
        N'ajoute PAS les items a une scene : c'est le role de show().
        A reimplementer dans chaque sous-classe.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # construction du menu
    # ------------------------------------------------------------------

    def _build_menu(self):
        from game.ui.sprite_button import SpriteButton

        self._btns = []
        btn_h   = TILE_SIZE
        spacing = int(self._menu_spacing * SCALE)
        start_y = int(_SCENE_H * self._menu_start_ratio)
        btn_w   = 7 * TILE_SIZE
        btn_x   = (_SCENE_W - btn_w) // 2

        for i, entry in enumerate(self._menu):
            y = start_y + i * (btn_h + spacing)
            btn = SpriteButton(
                label   = entry["label"],
                x       = btn_x,
                y       = y,
                enabled = entry.get("enabled", True),
            )
            self._btns.append(btn)
            self._items.extend(btn.get_items())

    # ------------------------------------------------------------------
    # rafraichissement visuel
    # ------------------------------------------------------------------

    def _refresh_highlight(self):
        for i, btn in enumerate(self._btns):
            if i == self._selected:
                btn.set_state("selected")
            else:
                btn.set_state("normal")

    # ------------------------------------------------------------------
    # navigation clavier
    # ------------------------------------------------------------------

    def key_press(self, key):
        if key == KEYS["DOWN"]:
            self._move(+1)
        elif key == KEYS["UP"]:
            self._move(-1)
        elif key in (KEYS["INTERACT"], KEYS["CONFIRM"]):
            self._press_selected()

    def key_release(self, key):
        if key in (KEYS["INTERACT"], KEYS["CONFIRM"]):
            self._release_selected()

    def _move(self, direction):
        n = len(self._menu)
        if n == 0:
            return
        old   = self._selected
        index = self._selected
        for _ in range(n):
            index = (index + direction) % n
            if self._menu[index].get("enabled", True):
                break
        if index != old:
            self._selected = index
            self._refresh_highlight()
            self._play_sfx("snd_choice")

    def _press_selected(self):
        if not self._btns:
            return
        if not self._menu[self._selected].get("enabled", True):
            return
        self._btns[self._selected].set_state("pressed")
        self._is_pressed = True

    def _release_selected(self):
        if not self._is_pressed:
            return
        self._is_pressed = False
        self._refresh_highlight()
        self._activate()

    # ------------------------------------------------------------------
    # navigation souris
    # ------------------------------------------------------------------

    def mouse_press(self, scene_pos):
        for i, btn in enumerate(self._btns):
            if not self._menu[i].get("enabled", True):
                continue
            if btn.contains(scene_pos):
                self._selected = i
                self._refresh_highlight()
                btn.set_state("pressed")
                self._activate()
                return

    # ------------------------------------------------------------------
    # activation et dispatch
    # ------------------------------------------------------------------

    def _activate(self):
        self._dispatch(self._menu[self._selected]["action"])

    def _dispatch(self, action):
        pass

    # ------------------------------------------------------------------
    # utilitaires
    # ------------------------------------------------------------------

    def _play_sfx(self, name):
        sm = self.screen_manager
        if sm._scene and hasattr(sm._scene, 'sfx_manager'):
            sm._scene.sfx_manager.play(name)

    def _select_first_enabled(self):
        for i, entry in enumerate(self._menu):
            if entry.get("enabled", True):
                self._selected = i
                return

    @property
    def is_visible(self):
        return self._visible