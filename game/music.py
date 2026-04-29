# -*- coding: utf-8 -*-

from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import QUrl, QTimer
import os

from game.config import DEBUG, DURATION_FADE_OUT_ROOM

class MusicManager:
    def __init__(self):
        self.player = QSoundEffect()
        self.player.setLoopCount(QSoundEffect.Infinite)

        self.player.statusChanged.connect(self.on_status_changed)

        self.current_music = None
        self.pending_music = None

        self.target_volume = 1.0
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

    def play_mp3(self, music_name, fade_in = 0):
        """
        certains fichiers musicaux sont trop lourds en wav (>25mb), donc mp3
        """
        music_path = os.path.join(self.base_path, f"{music_name}.mp3")

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
        music_path = f"mus/{music_name}.wav"
        self.pending_music = None

        if DEBUG:
            print(f"[MUSIC] Loading async {music_path}")

        url = QUrl.fromLocalFile(os.path.abspath(music_path))
        self.player.setSource(url)
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
            
            init_fade_in = 0.1 # 0 null, 1 max, ici demarre a 10%, a pas changer
            
            t = min(self.timer / self.fade_in_duration, 1.0)
            current_factor = init_fade_in + (t * (1.0 - init_fade_in))
            volume = current_factor * self.target_volume
            self.player.setVolume(max(0.0, volume))
            
            if t >= 1.0:
                self.player.setVolume(self.target_volume)
                self.state = "idle"

    def stop(self):
        self.player.stop()
        self.current_music = None
        self.pending_music = None
        
    def start_fade_out(self):
        if self.player.isPlaying():
            self.state = "fade_out"
            self.timer = 0