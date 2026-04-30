# # -*- coding: utf-8 -*-
# import os
# from PyQt5.QtMultimedia import QSoundEffect
# from PyQt5.QtCore import QUrl
# from game.config import DEBUG

# class SFXManager:
#     def __init__(self):
#         self.sounds = {}
#         self.base_path = "sound_effect"
#         self.default_volume = 0.95
        
#         self._preload_all_sounds()

#     def _preload_all_sounds(self):
#         """
#         charge automatiquement tous les sons au lancement du jeu
#         car sinon probleme lorsque son se joue car est cherche a chaque fois et freeze
#         moins pb pour musiques car invoquees moins sousvent
#         """
#         if not os.path.exists(self.base_path):
#             if DEBUG:
#                 print(f"[SFX] Erreur : Le dossier '{self.base_path}' est introuvable.")
#             return

#         files = [f for f in os.listdir(self.base_path) if f.endswith(".wav")]
        
#         for filename in files:
#             name = os.path.splitext(filename)[0] # "nom.wav" -> "nom"
#             path = os.path.join(self.base_path, filename)
            
#             effect = QSoundEffect()

#             url = QUrl.fromLocalFile(os.path.abspath(path))
#             effect.setSource(url)
#             effect.setVolume(self.default_volume)
#             effect.setLoopCount(0)
            
#             self.sounds[name] = effect
            
#             if DEBUG:
#                 print(f"[SFX] Son chargé : {name} ({path})")

#         if DEBUG:
#             print(f"[SFX] Total : {len(self.sounds)} sons chargés.")

#     def play(self, name):
#         """Joue son par son nom"""
#         if name in self.sounds:
#             # Si son deja en cours le relance du début
#             self.sounds[name].play()
#         elif DEBUG:
#             print(f"[SFX] Erreur : Le son '{name}' n'existe pas dans le dictionnaire.")

#     def set_volume(self, volume):
#         """Ajuste le volume global des bruitages (0.0 à 1.0)."""
#         self.default_volume = max(0.0, min(1.0, volume))
#         for sound in self.sounds.values():
#             sound.setVolume(self.default_volume)


"""
sfx geres separements avec pygame (autorisation recu en cours)
"""

# -*- coding: utf-8 -*-

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from game.config import DEBUG

class SFXManager:
    def __init__(self):
        # 48kHz, 16-bit signé, stereo
        try:
            pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32) # autorise 32 sons simultanés
        except Exception as e:
            if DEBUG:
                print(f"[SFX] Erreur lors de l'initialisation du mixer : {e}")

        self.sounds = {}
        self.base_path = "sound_effect"
        self.default_volume = 0.8
        
        self._preload_all_sounds()

    def _preload_all_sounds(self):
        """
        charge automatiquement tous les sons au lancement du jeu
        car sinon probleme lorsque son se joue car est cherche a chaque fois et freeze
        moins pb pour musiques car invoquees moins souvent
        """
        if not os.path.exists(self.base_path):
            if DEBUG:
                print(f"[SFX] Erreur : Le dossier '{self.base_path}' est introuvable.")
            return

        files = [f for f in os.listdir(self.base_path) if f.endswith(".wav")]
        
        for filename in files:
            name = os.path.splitext(filename)[0] # "nom.wav" -> "nom"
            path = os.path.join(self.base_path, filename)
            
            try:
                # Charge le son directement en mémoire vive via pygame
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.default_volume)
                
                self.sounds[name] = sound
                
                if DEBUG:
                    print(f"[SFX] Son chargé : {name} ({path})")
            except Exception as e:
                if DEBUG:
                    print(f"[SFX] Erreur lors du chargement de {name} : {e}")

        if DEBUG:
            print(f"[SFX] Total : {len(self.sounds)} sons chargés.")

    def play(self, name):
        """Joue son par son nom"""
        if name in self.sounds:
            # Joue sur le premier canal disponible (ne bloque jamais le CPU)
            # Si le son est déjà en cours, pygame peut le superposer ou le relancer
            self.sounds[name].play()
        elif DEBUG:
            print(f"[SFX] Erreur : Le son '{name}' n'existe pas dans le dictionnaire.")

    def set_volume(self, volume):
        """Ajuste le volume global des bruitages (0.0 à 1.0)."""
        self.default_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.default_volume)