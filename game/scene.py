# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPen
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from game.player import Player
import time

from game.room_loader import load_room
from game.transition import TransitionManager
from game.music import MusicManager
from game.sfx import SFXManager

from game.tileset import TILE_TYPES
from game.config import SCALE, BASE_TILE_SIZE, TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, FPS, interval, DEBUG

from game.player import Player
#from game.enemies.placeholder1 import Placeholder1
from game.enemies.enemy_registry import ENEMY_TYPES

# offset de placement lorsque transition ecran
OFFSET = 2 # pixels

# --- SCENE ---
class GameScene(QGraphicsScene):
    def __init__(self):
        super().__init__()

        width = GRID_WIDTH * TILE_SIZE
        height = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE

        self.setSceneRect(0, 0, width, height)
        
        self.tileset = {}
        self.current_biome = None
        
        # # --- TILESET -- pixmap
        # self.tileset = {
        #     0: QPixmap("assets/sand.png").scaled(
        #         TILE_SIZE,
        #         TILE_SIZE,
        #         transformMode=Qt.FastTransformation
        #     ),
        #     1: QPixmap("assets/tree.png").scaled(
        #         TILE_SIZE,
        #         TILE_SIZE,
        #         transformMode=Qt.FastTransformation
        #     )
        # }
        

        self.draw_hud()
        
        # --- PLAYER 
        self.player = Player(SCALE)
        self.addItem(self.player)
        
        self.enemies = []
        
        self.room_states = {}
        room = load_room("rooms/room3.json") #room initiale
        self.current_room = "room3"
        self.room_data = room
        self.draw_room(room)
        
        self.transition = TransitionManager(self)


        
        # coordonées commencent sous hud
        self.player.y += HUD_HEIGHT * TILE_SIZE
        
        self.is_transitioning = False
        
        if DEBUG:
            self.addItem(self.player.debug_rect)
        
        # --- GAME LOOP ---
        self.last_time = time.time()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(interval)
        
        # music 
        self.music_manager = MusicManager()
        self.pending_music = None
        self.sfx_manager = SFXManager()
        
        # etats des rooms
        self.room_states = {}

        
        # IMPORTANT ! items persistant, à ajouter pour conservation lors de chgmt de salle
        self.persistent_items = {
            self.player,
            self.transition.overlay,
            self.player.exit_label
        }
        
        if DEBUG:
            self.persistent_items.add(self.player.debug_rect)
        

    def draw_hud(self):
        width = GRID_WIDTH * TILE_SIZE
        height = HUD_HEIGHT * TILE_SIZE
        
        hud = QGraphicsRectItem(0, 0, width, height)
        hud.setBrush(QBrush(QColor("#000000")))
        hud.setPen(QColor("#000000"))
        
        hud.setZValue(1000) # car sinon problème quand ennemi a hauteur de 2, passe au dessus
        
        self.addItem(hud)


    def game_loop(self):
        
        #on n'update pas si mort
        if getattr(self, "game_over_triggered", False):
            return 
        
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        if not self.is_transitioning:
            self.player.update(dt, self)
            self.check_room_transition()
        
            if hasattr(self, "enemies"):
                for enemy in self.enemies:
                    enemy.update(dt, self)
            
        # if not self.is_transitioning:
        #     self.player.update(dt, self)
        #     self.check_room_transition()
            
        #     for enemy in self.enemies:
        #         enemy.update(dt, self)
    
        self.transition.update(dt)
        self.music_manager.update(dt)

    def is_blocking_rect(self, x, y, w, h):
        """
        

        Parameters
        ----------
        x,y : coordonées sur personnage(en haut a gauche)
        w,h : largeur et hauteur pour definir hitbox
        Returns
        -------
        bool
            y a t il collision ou non.

        """
        # coins du rectangle
        points = [
            (x, y),
            (x + w, y),
            (x, y + h),
            (x + w, y + h)
        ]
    
        transitions = self.room_data.get("transitions", {})
    
        for px, py in points:
            tile_x = int(px // TILE_SIZE)
            tile_y = int((py - HUD_HEIGHT * TILE_SIZE) // TILE_SIZE)
    
            if tile_x < 0:
                if transitions.get("left"):
                    continue
                return True
    
            if tile_x >= GRID_WIDTH:
                if transitions.get("right"):
                    continue
                return True
    
            if tile_y < 0:
                if transitions.get("up"):
                    continue
                return True
    
            if tile_y >= GRID_HEIGHT:
                if transitions.get("down"):
                    continue
                return True
    
            tile_id = self.room_data["tiles"][tile_y][tile_x]
    
            if TILE_TYPES[tile_id]["collision"] == 1:
                return True
    
        return False


    def load_biome_tileset(self, biome_name):
        """
        Fonction qui recupere le biome de la salle et update current_loaded_biome
        """
        # si le biome en chargement les le meme que current biome, on ne fait rien
        if hasattr(self, 'current_loaded_biome') and self.current_loaded_biome == biome_name:
            return 
        
        if DEBUG:
            print(f"Changement de biome détecté : chargement de {biome_name}...")
        
        self.tileset = {}
        
        for tile_id, props in TILE_TYPES.items():
            tile_filename = f"{props['name']}.png"
            
            path = f"assets/{biome_name}/{tile_filename}"
            pix = QPixmap(path)
            
            # backup si chemin non trouve, on utilise default
            if pix.isNull() and biome_name != "default":
                path_fallback = f"assets/default/{tile_filename}"
                pix = QPixmap(path_fallback)
                if DEBUG and not pix.isNull():
                    print(f"  > Tile '{props['name']}' non trouvée dans {biome_name}, utilisation du dossier default.")
            
            if not pix.isNull():
                self.tileset[tile_id] = pix.scaled(
                    TILE_SIZE, TILE_SIZE, 
                    transformMode=Qt.FastTransformation
                )

        self.current_loaded_biome = biome_name


    def draw_room(self, room):
        """
        invoquee par _change_room_internal et prend en parametre la room
        dessine salle suivante avec ses tiles
        
        On rempli la room du sol (ground.png id = 0)
        on place par dessus les autres assets en fonction du biome
        On a pas securite biome default
        """
        biome_actuel = room.get("biome", "default")
        self.load_biome_tileset(biome_actuel)
        
        ground_pixmap = self.tileset.get(0)

        for y, row in enumerate(room["tiles"]):
            for x, tile_id in enumerate(row):
                
                # dessins du sol d'abord
                if ground_pixmap:
                    ground_item = QGraphicsPixmapItem(ground_pixmap)
                    ground_item.setPos(
                        x * TILE_SIZE,
                        (y + HUD_HEIGHT) * TILE_SIZE
                    )
                    self.addItem(ground_item)
                    ground_item.setZValue(0)

                if tile_id != 0:
                    pixmap = self.tileset.get(tile_id)
                    
                    if pixmap:
                        item = QGraphicsPixmapItem(pixmap)
                        item.setPos(
                            x * TILE_SIZE,
                            (y + HUD_HEIGHT) * TILE_SIZE
                        )
                        self.addItem(item)
                        item.setZValue(1)

                        if DEBUG and TILE_TYPES[tile_id]["collision"] == 1:
                            rect = QGraphicsRectItem(
                                x * TILE_SIZE,
                                (y + HUD_HEIGHT) * TILE_SIZE,
                                TILE_SIZE, TILE_SIZE
                            )
                            rect.setPen(QPen(QColor("blue"), 1))
                            rect.setZValue(500)
                            self.addItem(rect)
        
        self.spawn_enemies(room)
        
    def _change_room_internal(self, room_name, direction):
        """
        Fonction de changement de salle
        On load la room suivante,
        met la scene en etat de transition pour freeze,
        nettoie la scene,
        reddessine la scene avec draw_room
        
        utilisee lors de transition.update()

        Parameters
        ----------
        room_name : voir fichier json
        direction : str, direction de la transition - voir check_room_transition()

        """
        room = load_room(f"rooms/{room_name}.json")
        self.current_room = room_name
        self.is_transitioning = True
        self.room_data = room
        self.enemies = []
    
        # nettoyer scene (items persistants), conserver joueur, ecran, fondu... lors de chgmt
        for item in list(self.items()):
            if item not in self.persistent_items: 
                self.removeItem(item)

        self.draw_hud()
        self.draw_room(room)
    
        self.reposition_player(direction)
    
    def check_room_transition(self):
        if self.is_transitioning: #check pour empecher transitions multiples
            return 
        
        hx, hy, hw, hh = self.player.get_hitbox() # permet de faire transition par hitbox et non position
    
        room_w = GRID_WIDTH * TILE_SIZE
        #room_h = GRID_HEIGHT * TILE_SIZE
    
        transitions = self.room_data.get("transitions", {})
    
        if hx < 0:
            target = transitions.get("left")
            if target:
                self.transition.start(target, "left")
    
        elif hx + hw > room_w:
            target = transitions.get("right")
            if target:
                self.transition.start(target, "right")
    
        elif hy < HUD_HEIGHT * TILE_SIZE:
            target = transitions.get("up")
            if target:
                self.transition.start(target, "up")
    
        elif hy + hh > (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE:
            target = transitions.get("down")
            if target:
                self.transition.start(target, "down")
        
    
    """
    MUSIQUE! Toutes en wav 16-bits, sinon qt ne lance pas (pas ogg)
    """
        
    def start_room_music(self):
        """
        Fonction pour start musique, avec gestion fade in
        """
        music = self.room_data.get("music")
        
        fade_in_value = self.room_data.get("fade_in", 0)
    
        if music:
            name = f"{music}"
            self.music_manager.play(name, fade_in=fade_in_value)
    
    def room_music_changed(self):
        """
        Fonciton pour changer le chemin de la musique a jouer, 
        ne joue rien en tant que tel
        Sert après changement de salle
        """
        music = self.room_data.get("music")
    
        if not music:
            return False
    
        new_name = f"{music}"
    
        return self.music_manager.current_music != new_name

    def next_room_music_changed(self, room_name):
        """
        compare la musique de la future salle avec la musique actuelle
        Sert avant transition
        """

        room = load_room(f"rooms/{room_name}.json")
    
        next_music = room.get("music")
    
        if not next_music:
            return False
    
        next_mus = f"{next_music}"
    
        return self.music_manager.current_music != next_mus
    
    """
    FIN DE LA SECTION MUSIQUE
    """

    def reposition_player(self, direction):
        """
        Repositionne le joueur en fonciton de la direction a laquelle il est arrive
        on repositionne par rapport aux tiles,
        avec un OFFSET de quelques pixels pour eviter transitions en boucle
        on prend en compte la hitbox du joueur (en pratique ne change rien si = 1 tile)

        Parameters
        ----------
        direction : str

        """
        if direction == "left":
            self.player.x = GRID_WIDTH * TILE_SIZE - self.player.hitbox_width - OFFSET - self.player.hitbox_offset_x * TILE_SIZE
    
        elif direction == "right":
            self.player.x = OFFSET  - self.player.hitbox_offset_x * TILE_SIZE
    
        elif direction == "up":
            self.player.y = (GRID_HEIGHT + HUD_HEIGHT) * TILE_SIZE - self.player.hitbox_height  - self.player.hitbox_offset_y* TILE_SIZE - OFFSET
    
        elif direction == "down":
            self.player.y = HUD_HEIGHT * TILE_SIZE + OFFSET - self.player.hitbox_offset_y * TILE_SIZE
    
        self.player.update_graphics()

    def spawn_enemies(self, room):
        """
        Fonctionne comme les fonctions de generation de salle
        Cherche pour les ennemis dans le json et les fait spawn
        """
        self.enemies = []
        
        # on recupere ennemis tues dans la session
        killed = self.room_states.get(
            self.current_room, {}
            ).get("killed_enemies", set())
    
        for data in room.get("enemies", []):
            #si deja mort, pas spawn
            enemy_id = data["id"]
            if enemy_id in killed:
                continue
            
            enemy_type = data["type"]
            x = data["x"] * TILE_SIZE
            y = (data["y"] + HUD_HEIGHT) * TILE_SIZE
            
            # utilise enemy_registry.py pour obtenir liste des ennemis
            enemy_class = ENEMY_TYPES.get(enemy_type)
            if enemy_class is None:
                continue
            enemy = enemy_class(SCALE,x,y)
            # if enemy_type == "placeholder1":
            #     enemy = Placeholder1(SCALE, x, y)
    
            # else:
            #     continue  # inconnu
            
            enemy.enemy_id = data["id"]
            enemy.room_name = self.current_room
            
            enemy.set_target(self.player)
    
            self.enemies.append(enemy)
            self.addItem(enemy)
            
            # force affichange initial de l'ennemi avant fade_in
            enemy.update_graphics()
    
            if DEBUG:
                self.addItem(enemy.debug_rect)
                
    def game_over(self):
        if hasattr(self, "game_over_triggered") and self.game_over_triggered:
            return
    
        self.game_over_triggered = True
    
        #stop gameplay
        self.is_transitioning = True
    
        # stop musique actuelle
        self.music_manager.stop()
    
        # son gameover, avec loopcount = 1
        self.music_manager.player.setLoopCount(1)
        self.music_manager.play("mus_gameover", fade_in = 5)
    
        # clear tout
        for enemy in self.enemies:
            self.removeItem(enemy)
        self.enemies.clear()
    
        # ecran noir
        self.game_over_overlay = QGraphicsRectItem(
            self.sceneRect()
        )
        self.game_over_overlay.setBrush(QBrush(QColor(0, 0, 0)))
        self.game_over_overlay.setZValue(9999)
        self.addItem(self.game_over_overlay)
                