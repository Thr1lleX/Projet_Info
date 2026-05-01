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


class BaseScreen:
    """
    Classe abstraite dont heritent tous les ecrans.
    Ne pas instancier directement.
    """

    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self._items   = []     # QGraphicsItems de cet ecran (remplis dans _build)
        self._visible = False
        self._built   = False

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
    # evenements (a surcharger)
    # ------------------------------------------------------------------

    def key_press(self, key):
        """Traite un evenement clavier. key est un Qt.Key_xxx."""
        pass

    def mouse_press(self, scene_pos):
        """
        Traite un clic souris.
        scene_pos est un QPointF en coordonnees scene.
        """
        pass

    # ------------------------------------------------------------------
    # etat
    # ------------------------------------------------------------------

    @property
    def is_visible(self):
        return self._visible
