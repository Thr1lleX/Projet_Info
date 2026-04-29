# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt
from game.music import MusicManager
from game.config import DURATION_FADE_IN_ROOM, DURATION_FADE_OUT_ROOM


class TransitionManager:
    def __init__(self, scene):
        self.scene = scene

        self.state = "idle"
        self.timer = 0

        self.duration_out = DURATION_FADE_OUT_ROOM #float >0 
        self.duration_in = DURATION_FADE_IN_ROOM

        self.next_room = None
        self.direction = None
        
        rect = scene.sceneRect()
        
        self.overlay = QGraphicsRectItem(
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height()
        )

        self.overlay.setBrush(QBrush(QColor(0, 0, 0)))
        self.overlay.setOpacity(0)
        self.overlay.setZValue(2000)

        scene.addItem(self.overlay)
        self.is_transitioning = False
        
        # pour gerer transitions musique
        self.music_manager = MusicManager()
        self.music_freeze_duration = DURATION_FADE_IN_ROOM

    def start(self, room_name, direction):
        if self.state != "idle":
            return
    
        self.next_room = room_name
        self.direction = direction
    
        self.state = "fade_out"
        self.timer = 0
    
        self.scene.is_transitioning = True
        
        # si musique != salle suivante alors transition
        if self.scene.next_room_music_changed(room_name):
            self.scene.music_manager.fade_out_duration = self.duration_out
            self.scene.music_manager.start_fade_out()

    def update(self, dt):
        """
        permet de gerer transitions entre salles
        on fait dans cet ordre:
            fade out
            changement de salle - freeze
            fade in
            load musique
            
        on ne peut pas load la musique avant le fade in, sinon freeze le jeu trop long

        """
        if self.state == "idle":
            return
    
        self.timer += dt
    
        # --- FADE OUT ---
        if self.state == "fade_out":
            t = min(self.timer / self.duration_out, 1)
            self.overlay.setOpacity(t)
    
            if t >= 1:
                self.state = "change_room"
                self.timer = 0
    
        # --- CHANGE ROOM ---
        elif self.state == "change_room":
            self.scene._change_room_internal(self.next_room, self.direction)
    
            self.state = "fade_in"
            self.timer = 0
    
        # --- FADE IN ----
        elif self.state == "fade_in":
            t = min(self.timer / self.duration_in, 1)
            self.overlay.setOpacity(1 - t)
    
            if t >= 1:    
                # on débute le chargement de musique au fade in
                if self.scene.room_music_changed():
                    self.scene.start_room_music()
                    self.state = "music_wait"
                    self.timer = 0
                else:
                    self.state = "idle"
                    self.scene.is_transitioning = False

        # --- WAIT MUSIC LOAD ----
        elif self.state == "music_wait":
            if self.timer >= self.music_freeze_duration:
                self.state = "idle"
                self.scene.is_transitioning = False