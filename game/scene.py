# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QTimer
from game.player import Player
from game.hud import HUD
import time
import random

from game.room_loader import load_room
from game.transition import TransitionManager
from game.sfx import SFXManager

from game.tileset import TILE_TYPES
from game.config import BASE_TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, OFFSET
from game.config import FPS, interval, DEBUG

from game.settings import settings

from game.player import Player
from game.enemies.enemy_registry import ENEMY_TYPES
from game.animspr import load_animation_sequence
from game.poof_effect import PoofEffect

from game.save_manager import SaveManager
from game.interactables.interactable_registry import INTERACTABLE_TYPES
from game.dialogue_manager import DialogueManager



# --- SCENE ---
class GameScene(QGraphicsScene):
    def __init__(self, screen_manager=None):
        super().__init__()

        # reference vers le ScreenManager (definie ici ou par ScreenManager.set_scene)
        self.screen_manager = screen_manager

        # le jeu reste en pause jusqu'a ce que start_new_game() soit appele
        self.game_paused = True

        width = GRID_WIDTH * settings.tile_size
        height = (GRID_HEIGHT + HUD_HEIGHT) * settings.tile_size

        self.setSceneRect(0, 0, width, height)

        self.tileset = {}
        self.current_biome = None

        self.hud = HUD(self, self.screen_manager)
        self.dialogue_manager = DialogueManager(self)
        
        # --- PLAYER 
        self.player = Player(settings.scale)
        self.addItem(self.player)
        
        self.enemies = []
        self.interactables = []
        
        self.transition = TransitionManager(self)


        
        # coordonées commencent sous hud
        self.player.y += HUD_HEIGHT * settings.tile_size
        
        self.is_transitioning = False
        
        if DEBUG:
            self.addItem(self.player.debug_rect)
        
        
        # --- GAME LOOP ---
        self.last_time = time.time()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(interval)
        
        # music 
        self.music_manager = self.screen_manager.music_manager
        self.pending_music = None
        self.sfx_manager = SFXManager()
        
        # variables d'animation des tiles
        self.animated_tile_items = [] 
        self.animation_timer = 0
        self.frame_duree = 0.5 #duree de frame d'animation tile avant changement
        
        self.visual_effects = []
        self.magic_walls_poofed = False

        # save courante
        self.current_save = None
        
        # etats des rooms
        self.room_states = {}
        
        # flags sessions courante
        self.session_flags = {}
        
        # variables room
        self.current_room = None
        self.room_data = None
        # items droppes
        self.dropped_items = []                
        
        # IMPORTANT ! items persistant, a ajouter pour conservation lors de chgmt de salle
        self.persistent_items = {
            self.player,
            self.transition.overlay,  
            self.player.exit_label_shadow,
            self.player.exit_label_main
        }
        # les items du HUD doivent survivre aux changements de salle
        self.persistent_items.update(self.hud.get_items())

        self.update_crt(settings.crt_overlay)
        
        
        if DEBUG:
            self.persistent_items.add(self.player.debug_rect)
            

                    

    def game_loop(self):
        """
        toutes les updates de la scene
        """
        # last_time est mis a jour en premier pour eviter un grand dt au depause
        current_time = time.time()
        dt = min(current_time - self.last_time, 0.1)
        self.last_time = current_time

        if getattr(self, "game_over_triggered", False):
            return
        
        self.update_crt()
        
        for effect in self.visual_effects[:]:
            if effect.update(dt):
                self.removeItem(effect)
                self.visual_effects.remove(effect)
        
        # dialogue continue meme si jeu bloque
        self.dialogue_manager.update(dt)
        
        if self.game_paused:
            return

        if not self.is_transitioning:
            #gestion de surveillange du flag de magic_wall
            magic_flag = self.room_data.get("magic_wall")
            poofed_room_flag = f"magic_poofed_{self.current_room}"
            if magic_flag and self.get_flag(magic_flag) and not self.get_flag(poofed_room_flag):
                self.poof_all_magic_walls()
                
            self.player.update(dt, self)
            self.check_room_transition()
            self.update_animations(dt)
            
            for enemy in self.enemies:
                enemy.update(dt, self)
            self._check_pickups()                                     
            for interactable in self.interactables:
                interactable.update(dt)
  
        self.transition.update(dt)

            
        self.music_manager.update(dt)

        self.hud.update_hud(self.player, self.screen_manager.inventory, self)

    
    def _check_pickups(self):
        """Ramasse les items au sol si le joueur les touche."""
        px, py, pw, ph = self.player.get_hitbox()
        inventory = self.screen_manager.inventory

        for drop in self.dropped_items[:]:   # copie pour iterer en supprimant
            dx, dy, dw, dh = drop.get_rect()
            # collision AABB
            if (px < dx + dw and px + pw > dx and
                    py < dy + dh and py + ph > dy):
                if inventory.add_item(drop.item_id):
                    self.removeItem(drop)
                    self.sfx_manager.play("snd_item")
                    self.dropped_items.remove(drop)                                              
    

    def update_crt(self, is_enabled=None):
        """
        gere a la fois l'activation/desactivation via le menu et l'animation via le game_loop
        """
        if is_enabled is not None:
            if is_enabled:
                if not hasattr(self, 'crt_overlay'):
                    self._create_crt_overlay()
                self.crt_overlay.show()
            else:
                if hasattr(self, 'crt_overlay'):
                    self.crt_overlay.hide()
            return

        if hasattr(self, 'crt_overlay') and self.crt_overlay.isVisible():
            self.crt_overlay.setOpacity(random.uniform(0.1, 0.15))
            if random.random() < 0.1:
                y = self.crt_overlay.y()
                self.crt_overlay.setY((y + 1 * settings.scale) % 2)

    def _create_crt_overlay(self):
        """
        cree l'image CRT uniquement si on en a besoin
        """
        width = GRID_WIDTH * settings.tile_size
        height = (GRID_HEIGHT + HUD_HEIGHT) * settings.tile_size
        
        self.crt_overlay = QGraphicsPixmapItem()
        self.crt_overlay.setPixmap(QPixmap("assets/hud/scanlines.png").scaled(int(width), int(height)))
        self.crt_overlay.setPos(0, 0)
        self.crt_overlay.setZValue(9999)
        
        self.addItem(self.crt_overlay)
        self.persistent_items.add(self.crt_overlay)

    def is_blocking_rect(self, x, y, w, h, entity=None):
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
            tile_x = int(px // settings.tile_size)
            tile_y = int((py - HUD_HEIGHT * settings.tile_size) // settings.tile_size)
    
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
            
            tile = TILE_TYPES[tile_id]
            
            # jesus update
            if tile["name"] == "water" and entity.can_go_on_water:
                continue
            
            if tile["collision"] == 1:
                return True
        
        target_rect = QRectF(x, y, w, h)
        for obj in self.interactables:
            if obj.collision:
                if target_rect.intersects(obj.sceneBoundingRect()):
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
            name = props["name"]
            
            # code pour looper si animation de tiles
            if props.get("animated"):
                path = f"assets/{biome_name}/{name}"
                sequence = None
                
                try:
                    # on essaie dans le biome actuel
                    sequence = load_animation_sequence(path, (1, 1), None)
                except FileNotFoundError:
                    # si ca echoue, on tente le fallback dans default
                    if biome_name != "default":
                        path_fallback = f"assets/default/{name}"
                        try:
                            sequence = load_animation_sequence(path_fallback, (1, 1), None)
                            if DEBUG:
                                print(f"  > Séquence '{name}' non trouvée dans {biome_name}, utilisation du dossier default.")
                        except FileNotFoundError:
                            pass
                
                if sequence:
                    self.tileset[tile_id] = sequence
                elif DEBUG:
                    print(f"Erreur : Séquence introuvable pour {name}")
                
            # code standard pour 1 frame
            else:
                tile_filename = f"{name}.png"
                
                # 1e cas, chemin specifique au biome
                path = f"assets/{biome_name}/{tile_filename}"
                pix = QPixmap(path)
    
            
                
                # 2e cas, backup si chemin non trouve, on utilise default
                if pix.isNull() and biome_name != "default":
                    path_fallback = f"assets/default/{tile_filename}"
                    pix = QPixmap(path_fallback)
                    if DEBUG and not pix.isNull():
                        print(f"  > Tile '{props['name']}' non trouvée dans {biome_name}, utilisation du dossier default.")
                
                if not pix.isNull():
                    self.tileset[tile_id] = pix.scaled(
                        int(pix.width() * settings.scale), int(pix.height() * settings.scale), 
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
        
        # gesiton du flag magic_wall, si present supprime tile
        magic_flag = room.get("magic_wall")
        # flag pour check si on a deja poof dans salle
        poofed_room_flag = f"magic_poofed_{self.current_room}"   
        if magic_flag and self.get_flag(magic_flag):
            if self.get_flag(poofed_room_flag):
                for y, row in enumerate(room["tiles"]):
                    for x, tile_id in enumerate(row):
                        if tile_id == 8:
                            room["tiles"][y][x] = 0
                            
        ground_pixmap = self.tileset.get(0)
        
        
        # forcer l'etat des blocs dynamiques selon le flag
        blue_active = self.get_flag("blue_switch")
        for y, row in enumerate(room["tiles"]):
            for x, tile_id in enumerate(row):
                if tile_id in (6.1, 6.2):
                    room["tiles"][y][x] = 6.2 if blue_active else 6.1
                elif tile_id in (7.1, 7.2):
                    room["tiles"][y][x] = 7.1 if blue_active else 7.2
        
        # dessins du sol d'abord - pas d'animation
        if ground_pixmap:
            for y, row in enumerate(room["tiles"]):
                for x, _ in enumerate(row):
                    ground_item = QGraphicsPixmapItem(ground_pixmap)
                    ground_item.setPos(
                        x * settings.tile_size,
                        (y + HUD_HEIGHT) * settings.tile_size
                    )
                    ground_item.setZValue(TILE_TYPES[0].get("z", 0))
                    self.addItem(ground_item)
    
        # dessins des autres tiles
        for y, row in enumerate(room["tiles"]):
            for x, tile_id in enumerate(row):
    
                if tile_id == 0:
                    continue
                # suppression des murs brises
                if tile_id == 2.1:
                    wall_flag = f"broken_{self.current_room}_{x}_{y}"
                    
                    if self.current_save.get_flag(wall_flag) or self.session_flags.get(wall_flag):
                        tile_id = 2.2
                        self.room_data["tiles"][y][x] = 2.2
    
                data = self.tileset.get(tile_id)
                if not data:
                    continue
    
                # tile animee
                if isinstance(data, list):
                    pixmap = data[0]
                    item = QGraphicsPixmapItem(pixmap)
                    self.animated_tile_items.append((item, tile_id))
                    # on l'ajoute a la liste des objets a animer
    
                # tile statique
                else:
                    item = QGraphicsPixmapItem(data)
    
                item.setPos(
                    x * settings.tile_size,
                    (y + HUD_HEIGHT) * settings.tile_size
                )
    
                z_value = TILE_TYPES[tile_id].get("z", 1)
                item.setZValue(z_value)
    
                self.addItem(item)
    
                if DEBUG and TILE_TYPES[tile_id]["collision"] == 1:
                    rect = QGraphicsRectItem(
                        x * settings.tile_size,
                        (y + HUD_HEIGHT) * settings.tile_size,
                        settings.tile_size, settings.tile_size
                    )
                    rect.setPen(QPen(QColor("blue"), 1))
                    rect.setZValue(500)
                    self.addItem(rect)
    
        self.spawn_enemies(room)
        self.spawn_interactables(room)

    def update_animations(self, dt):
        self.animation_timer += dt
        frame_index = int(self.animation_timer / self.frame_duree)
    
        for item, tile_id in self.animated_tile_items:
            frames = self.tileset[tile_id]
            current_frame = frame_index % len(frames)
            item.setPixmap(frames[current_frame])
            
            
    # --- CHARGEMENT DES SALLES ---
        
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
        room = self.apply_conditional_transitions(room)
        self.current_room = room_name
        self.is_transitioning = True
        self.room_data = room
        self.enemies = []
        self.dropped_items = []
        self.magic_walls_poofed = False 
        self.visual_effects.clear()
    
        # netoyer frames animees
        self.animated_tile_items.clear()
        # nettoyer scene (items persistants), conserver joueur, ecran, fondu... lors de chgmt
        for item in list(self.items()):
            if item not in self.persistent_items: 
                self.removeItem(item)
        

        self.draw_room(room)
    
        self.reposition_player(direction)
    
    def check_room_transition(self):
        if self.is_transitioning: #check pour empecher transitions multiples
            return 
        
        hx, hy, hw, hh = self.player.get_hitbox() # permet de faire transition par hitbox et non position
    
        room_w = GRID_WIDTH * settings.tile_size
        #room_h = GRID_HEIGHT * settings.tile_size
    
        transitions = self.room_data.get("transitions", {})
    
        if hx < 0:
            target = transitions.get("left")
            if target:
                self.transition.start(target, "left")
    
        elif hx + hw > room_w:
            target = transitions.get("right")
            if target:
                self.transition.start(target, "right")
    
        elif hy < HUD_HEIGHT * settings.tile_size:
            target = transitions.get("up")
            if target:
                self.transition.start(target, "up")
    
        elif hy + hh > (GRID_HEIGHT + HUD_HEIGHT) * settings.tile_size:
            target = transitions.get("down")
            if target:
                self.transition.start(target, "down")

    def apply_conditional_transitions(self, room):
        """
        modifie les transitions selon les flags
        """
        
        transitions = room.get("transitions", {}).copy()
    
        for rule in room.get("conditional_transitions", []):
    
            flag = rule["flag"]
    
            if self.current_save.get_flag(flag):
    
                direction = rule["direction"]
                target = rule["target"]
    
                transitions[direction] = target
    
        room["transitions"] = transitions
    
        return room
        
    
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
    
    def toggle_crystal_blocks(self):
        """
        met a jour toutes les tiles bleues/rouges de la salle courante
        
        si blue_switch == True : Bleu baisse (6.2), Rouge se leve (7.1)
        si blue_switch == False : Bleu se lève (6.1), Rouge baisse (7.2)
        """
        if not self.room_data:
            return
            
        blue_active = self.get_flag("blue_switch")
        
        for y, row in enumerate(self.room_data["tiles"]):
            for x, tile_id in enumerate(row):
                new_id = None
                
                if tile_id in (6.1, 6.2):
                    new_id = 6.2 if blue_active else 6.1
                elif tile_id in (7.1, 7.2):
                    new_id = 7.1 if blue_active else 7.2
                    
                if new_id and new_id != tile_id:
                    self.room_data["tiles"][y][x] = new_id
                    self.refresh_single_tile(x, y, new_id)

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
            self.player.x = GRID_WIDTH * settings.tile_size - self.player.hitbox_width - OFFSET - self.player.hitbox_offset_x * settings.tile_size
    
        elif direction == "right":
            self.player.x = OFFSET  - self.player.hitbox_offset_x * settings.tile_size
    
        elif direction == "up":
            self.player.y = (GRID_HEIGHT + HUD_HEIGHT) * settings.tile_size - self.player.hitbox_height  - self.player.hitbox_offset_y* settings.tile_size - OFFSET
    
        elif direction == "down":
            self.player.y = HUD_HEIGHT * settings.tile_size + OFFSET - self.player.hitbox_offset_y * settings.tile_size
    
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
            
            spawn_if = data.get("spawn_if")
            despawn_if = data.get("despawn_if")
            
            # s'il faut un flag et qu'on ne l'a pas, on ne spawn pas
            if spawn_if and not self.get_flag(spawn_if):
                continue
            
            # s'il y a un flag d'interaction et qu'on l'a, on ne spawn pas
            if despawn_if and self.get_flag(despawn_if):
                continue
            
            enemy_type = data["type"]
            x = data["x"] * settings.tile_size
            y = (data["y"] + HUD_HEIGHT) * settings.tile_size
            
            # utilise enemy_registry.py pour obtenir liste des ennemis
            enemy_class = ENEMY_TYPES.get(enemy_type)
            if enemy_class is None:
                continue
            enemy = enemy_class(settings.scale,x,y)
            
            enemy.enemy_id = data["id"]
            enemy.room_name = self.current_room
            
            enemy.set_target(self.player)
            
            enemy.set_flag_on_death = data.get("set_flag")
    
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
        self.is_transitioning = True

        self.music_manager.stop()
        # son gameover, avec loopcount = 1
        self.music_manager.player.setLoopCount(1)
        self.music_manager.play("mus_gameover", fade_in=0)

        for enemy in self.enemies:
            self.removeItem(enemy)
        self.enemies.clear()
        # l'ecran de game over est gere par ScreenManager.on_game_over()
                
        

    def load_current_save(self):
    
        room_name = self.current_save.get_current_room()
    
        room = load_room(f"rooms/{room_name}.json")
        room = self.apply_conditional_transitions(room)
    
        self.current_room = room_name
        self.room_data = room
    
        self.enemies = []
        self.animated_tile_items.clear()
    
        for item in list(self.items()):
            if item not in self.persistent_items:
                self.removeItem(item)
    
        self.draw_room(room)
    
        px, py = self.current_save.get_player_position()
        
        current_health = self.current_save.get_current_health()
        self.player.pv_main = current_health
    
        self.player.x = px * settings.tile_size
        self.player.y = (py + HUD_HEIGHT) * settings.tile_size
    
        self.player.update_graphics()
        
        # chargement inventaire
        inv_data = self.current_save.data.get("inventory")
        flags = self.current_save.data.get("flags", {})
        
        if inv_data is not None:
            self.screen_manager.inventory.from_save_data(inv_data)
        self.screen_manager.inventory.sync_permanent_items(flags)
            
    def try_break_tile(self, tile_x, tile_y):
        """
        detruit une tile aux coordonnes de la grille
        """
        if not (0 <= tile_x < GRID_WIDTH and 0 <= tile_y < GRID_HEIGHT):
            return

        tile_id = self.room_data["tiles"][tile_y][tile_x]
        tile_info = TILE_TYPES.get(tile_id)

        if tile_info and tile_info.get("breakable"):

            self.room_data["tiles"][tile_y][tile_x] = 2.2
            

            wall_flag = f"broken_{self.current_room}_{tile_x}_{tile_y}"
            self.session_flags[wall_flag] = True

            self.refresh_single_tile(tile_x, tile_y, 2.2)
            
    def poof_all_magic_walls(self):
        """
        dans une meme piece
        """
        poofed_room_flag = f"magic_poofed_{self.current_room}"
        for y, row in enumerate(self.room_data["tiles"]):
            for x, tile_id in enumerate(row):
                if tile_id == 8:
                    self.room_data["tiles"][y][x] = 0
                    
                    self.refresh_single_tile(x, y, 0)
                    
                    effect = PoofEffect(x, y)
                    self.addItem(effect)
                    self.visual_effects.append(effect)
        self.session_flags[poofed_room_flag] = True
        self.sfx_manager.play("snd_poof")

    def refresh_single_tile(self, tx, ty, new_id):
        """
        supprime l'ancien sprite a (tx, ty) et place le nouveau
        """
        px = tx * settings.tile_size
        py = (ty + HUD_HEIGHT) * settings.tile_size
        
        for item in self.items(QRectF(px, py, settings.tile_size, settings.tile_size)):
            if type(item) is QGraphicsPixmapItem and item not in self.persistent_items:
                self.removeItem(item)
        
        pix = self.tileset.get(new_id)
        if pix:
            new_item = QGraphicsPixmapItem(pix)
            new_item.setPos(px, py)
            new_item.setZValue(TILE_TYPES[new_id].get("z", 0))
            self.addItem(new_item)
        
    def load_save(self, slot=1):
        self.session_flags.clear()
        self.current_save = SaveManager(slot)
        self.load_current_save()
        
    
    def spawn_interactables(self, room):
        self.interactables = []
        current_biome = room.get("biome", "default")
        for data in room.get("interactables", []):
            interactable_type = data.get("type")
            interactable_class = INTERACTABLE_TYPES.get(interactable_type)

            if interactable_class is None:
                if DEBUG: print(f"Interactable inconnu : {interactable_type}")
                continue

            x = data["x"] * settings.tile_size
            y = (data["y"] + HUD_HEIGHT) * settings.tile_size

            if interactable_type == "npc":
                interactable = interactable_class(
                    settings.scale, 
                    x, 
                    y, 
                    data.get("npc_type"), 
                    data.get("dialogue"),
                    data.get("conditional_dialogue")
                )
            
            elif interactable_type == "sign":
                interactable = interactable_class(settings.scale, x, y, data.get("dialogue"),data.get("conditional_dialogue"))
            
            elif interactable_type == "chest":
                interactable = interactable_class(settings.scale, x, y, data.get("loot"), self.current_room)
                
                # chech etat initial
                if self.get_flag(interactable.flag_name):
                    interactable.is_open = True
                interactable.update_graphics()
                
            elif interactable_type == "locked_door":
                interactable = interactable_class(settings.scale, data.get("x"), data.get("y"),self.current_room,current_biome)
                if self.get_flag(interactable.flag_name):
                    interactable.is_open = True
                interactable.update_graphics()
            else:
                interactable = interactable_class(settings.scale, x, y)

            interactable.interactable_id = data.get("id")
            self.interactables.append(interactable)
            self.addItem(interactable)
            interactable.update_graphics()
            
            if DEBUG and hasattr(interactable, "debug_rect"):
                interactable.debug_rect.show()
                
    def save_game(self, slot):
        """
        sauvegarde la partie dans un slot
        """
        
        for flag_name, value in self.session_flags.items():
            self.current_save.set_flag(flag_name, value)
    
        data = {
            "current_room": self.current_room,
            "current_health": self.player.pv_main,
            "player_x": round(
                self.player.x / settings.tile_size,
                2
            ),
            "player_y": round(
                (
                    self.player.y
                    - HUD_HEIGHT * settings.tile_size
                ) / settings.tile_size,
                2
            ),
            "flags": self.current_save.data.get(
                "flags",
                {}
            ),
            "inventory": self.screen_manager.inventory.to_save_data()
        }
        SaveManager.write_save(slot, data)
        
        # on lie la sessions actuelle a ce slot
        self.current_save = SaveManager(slot)
    
        if DEBUG:
            print(f"Sauvegarde écrite : slot {slot}")

    def get_flag(self, flag_name):
        """
        verifie si un flag est actif en session ou en sauvegarde avec priorite sur session
        """
        if flag_name in self.session_flags:
            return self.session_flags[flag_name]
        return self.current_save.get_flag(flag_name)
        #return self.session_flags.get(flag_name) or self.current_save.get_flag(flag_name)