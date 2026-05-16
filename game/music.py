# -*- coding: utf-8 -*-
# Auteur : essentiellement Mateo

from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import QUrl, QTimer
import os

from game.config import DEBUG, DURATION_FADE_OUT_ROOM
from game.settings import settings

class MusicManager:
    def __init__(self):
        self.player = QSoundEffect()
        self.player.setLoopCount(QSoundEffect.Infinite)

        self.player.statusChanged.connect(self.on_status_changed)

        self.current_music = None
        self.pending_music = None

        self.target_volume = settings.music_volume
        self.state = "idle"
        self.timer = 0
        
        self.fade_in_duration = 0
        self.fade_out_duration = DURATION_FADE_OUT_ROOM #on met pareil pour harmoniser
        
        self.base_path = "mus"

    def on_status_changed(self):
        status = self.player.status()

        if status == QSoundEffect.Ready:
            if DEBUG:
                print("[MUSIC] Ready -> play")
            self.player.play()

        elif status == QSoundEffect.Error:
            print("[MUSIC] Error loading sound")

    def play(self, music_name, fade_in = 0):
        """
        joue musique wav avec fide_in suivant le nom de la musique dans dossier mus
        """
        music_path = os.path.join(self.base_path, f"{music_name}.wav")

        if not os.path.exists(music_path):
            return

        if self.current_music == music_name:
            return

        # priorite fluidite :
        # on stop immédiatement
        self.player.stop()
        self.current_music = None

        # on memorise la prochaine musique
        self.pending_music = music_name
        
        if fade_in > 0:
            self.fade_in_duration = fade_in
            self.state = "fade_in"
            self.timer = 0
        else: 
            self.state = "idle"

        # chargement après la frame actuelle
        QTimer.singleShot(0, self._load_pending)

    
    def _load_pending(self):
        if not self.pending_music:
            return

        music_name = self.pending_music
        
        path_wav = os.path.join(self.base_path, f"{music_name}.wav")
        
        if os.path.exists(path_wav):
            music_path = path_wav
        elif DEBUG:
            print(f"[MUSIC] Error: {music_name} introuvable en .wav")
        
        
        self.pending_music = None

        if DEBUG:
            print(f"[MUSIC] Loading async {music_path}")

        url = QUrl.fromLocalFile(os.path.abspath(music_path))
        

        self.player.setSource(url)
        
        if self.state == "fade_in":
            initial_vol = 0.1 * self.target_volume 
            self.player.setVolume(initial_vol)
        else:
            self.player.setVolume(self.target_volume)

        self.current_music = music_name

    def update(self, dt):
    
        if self.state == "fade_out":
    
            self.timer += dt
    
            t = min(self.timer / self.fade_out_duration, 1.0)
    
            volume = (1.0 - t) * self.target_volume
            self.player.setVolume(max(0.0, volume))
    
            if t >= 1.0:
                self.player.stop()
                self.player.setVolume(self.target_volume)
                self.state = "idle"
                
        # fade_in non initialise à 0
        elif self.state == "fade_in":
            self.timer += dt
            
            init_fade_in_ratio = 0.1 # 0 null, 1 max, ici demarre a 10%, a pas changer
            
            t = min(self.timer / self.fade_in_duration, 1.0)
            current_factor = init_fade_in_ratio + (t * (1.0 - init_fade_in_ratio))
            volume = current_factor * self.target_volume
            self.player.setVolume(max(0.0, volume))
            
            if t >= 1.0:
                self.player.setVolume(self.target_volume)
                self.state = "idle"

    def set_volume(self, volume):
        """
        Definit le volume cible (0.0 - 1.0).
        Si aucun fondu n'est en cours, applique immediatement.
        """
        self.target_volume = max(0.0, min(1.0, volume))
        if self.state == "idle":
            self.player.setVolume(self.target_volume)

    def stop(self):
        self.player.stop()
        self.current_music = None
        self.pending_music = None
        
    def start_fade_out(self):
        if self.player.isPlaying():
            self.state = "fade_out"
            self.timer = 0
