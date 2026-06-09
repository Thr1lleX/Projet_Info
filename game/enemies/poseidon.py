# -*- coding: utf-8 -*-
import math
import random
from PyQt5.QtGui import QPixmap,QPainter,QColor
from PyQt5.QtCore import Qt, QTimer

from game.enemies.enemy import Enemy
from game.config import BASE_TILE_SIZE, HUD_HEIGHT
from game.settings import settings
# Remplace cet import par le chemin où tu as rangé la classe Trident
from game.attacks.trident import Trident 
from game.animspr import load_animation_sequence

class Poseidon(Enemy):
    def __init__(self, scale, x, y):
        self._x = 0
        self._y = 0
        
        super().__init__(scale, x, y)

        # --- STATS DE BASE ---
        self._pv_max = 30
        self.pv_main = self._pv_max
        self.aggro_range = settings.tile_size * 16
        self.speed = 0 # Ne se deplace pas classiquement
        self.can_go_on_water = True
        self.use_pathfinding = False # On désactive l'A* de l'ennemi standard
        
        # --- ENRAGED / BUFF STATE ---
        self.speed_multiplier = 1.0
        
        base_path = "assets/enemies/poseidon/"
        self.taille_boss = (1,1)
        self.death_cry ="snd_death_poseidon"

        # Idle (3 frames)
        self.anim_idle_up = load_animation_sequence(f"{base_path}poseidon_back", self.taille_boss, 3)
        self.anim_idle_down = load_animation_sequence(f"{base_path}poseidon_face", self.taille_boss, 3)
        
        # Sortie / Plongée (9 frames)
        self.anim_sortie_up = load_animation_sequence(f"{base_path}poseidon_sortie_back", self.taille_boss, 9)
        self.anim_sortie_down = load_animation_sequence(f"{base_path}poseidon_sortie_face", self.taille_boss, 9)

        # --- MACHINE A ETATS & PATTERNS ---
        self.fps = 9.0
        self.anim_frame_timer = 0.0
        self.current_frame_index = 0
        
        # Etats possibles: "emerging", "charging", "idle_pause", "diving", "hidden"
        self.phase = "emerging" 
        self.state_timer = 1.0 # 9 frames / 9 fps = 1 seconde pour la sortie initiale
        
        # "multi" ou "simple" (commence necessairement par multi)
        self.current_attack = "multi" 
        self.visual_dir = "up"
        self.is_invulnerable = False
        
        # Initialisation sur la première frame de sortie
        self.setPos(self.x, self.y)
        if self.anim_sortie_up:
            self.setPixmap(self.anim_sortie_up[0])
    
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        # Limite x dans les tuiles de coordonnées [2, 13]
        min_x = 2 * settings.tile_size
        max_x = 13 * settings.tile_size
        self._x = max(min_x, min(value, max_x))

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        # Limite y dans les tuiles de coordonnées [1, 9]
        min_y = (1+HUD_HEIGHT) * settings.tile_size
        max_y = (9+HUD_HEIGHT) * settings.tile_size
        self._y = max(min_y, min(value, max_y))

    def take_damage(self, scene, damage, source=None):
        """ 
        Surcharge pour gerer l'insensibilite sous l'eau. 
        """
        if self.is_invulnerable:
            return
        super().take_damage(scene, damage, source)
    
    def _update_visual_direction(self):
        """
        il regarde vers le haut si le joueur l'a complètement dépasse
        idem vers le bas
        """
        if not self.target:
            return

        player_y = self.target.y
        player_hitbox_h = getattr(self.target, 'hitbox_height', settings.tile_size)
        boss_h = self.taille_boss[1] * settings.tile_size

        if self.visual_dir == "down":
            # S'il regarde vers le bas (face), le joueur doit passer entierement 
            # au-dessus de sa tete pour qu'il se retourne vers le haut (back)
            if player_y + player_hitbox_h < self.y:
                self.visual_dir = "up"
                
        elif self.visual_dir == "up":
            # S'il regarde vers le haut (back), le joueur doit passer entierement
            # en dessous de ses pieds pour qu'il se retourne vers le bas (face)
            if player_y > self.y + boss_h:
                self.visual_dir = "down"
                
    def setPixmap(self, pixmap):
        """ Intercepte les textures d'animations pour appliquer les effets visuels à la volee """
        if not pixmap or pixmap.isNull():
            super().setPixmap(pixmap)
            return
        
        if hasattr(self, 'phase') and self.phase in ["dying_dialogue", "dying_dive"]:
            super().setPixmap(pixmap)
            return

        # flash rouge
        if getattr(self, "is_damaged", False):
            tinted = pixmap.copy()
            painter = QPainter(tinted)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(tinted.rect(), QColor(255, 0, 0, 120))
            painter.end()
            super().setPixmap(tinted)
            return

        # clignotement blanc
        if getattr(self, "is_invulnerable", False):
            blink_delay = 0.7
            blink_speed = 0.3
            if self.invuln_timer >= blink_delay:
                if int((self.invuln_timer - blink_delay) / blink_speed) % 2 == 0:
                    tinted = pixmap.copy()
                    painter = QPainter(tinted)
                    painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
                    painter.fillRect(tinted.rect(), QColor(255, 255, 255, 45))
                    painter.end()
                    super().setPixmap(tinted)
                    return

        super().setPixmap(pixmap)
        
    def update_graphics(self):
        """ 
        Surcharge essentielle : empeche la classe parente (Enemy/Entity) 
        d'ecraser le pixmap de Poseidon avec son sprite de placeholder standard.
        """
        pass

    def update(self, dt, scene):
        if self._update_death_sequence(dt, scene):
            return
        # 1. Gerer les états bloquants (Stun, Knockback) s'il est vulnerable
        if not self.is_invulnerable:
            if self.kb_active:
                self.apply_knockback(dt, scene)
                self.update_graphics()
                self.update_damage_state(dt)
                return
            # ne peut pas etre stun
            # if self.is_stunned:
            #     self.apply_stun_wiggle(dt, scene)
            #     self.update_graphics()
            #     self.update_damage_state(dt)
            #     self.update_stun_animation(dt)
            #     return

        if not self.target:
            return
        
        # gestion de buff mi-vie (enraged)
        if self.pv_main <= self._pv_max / 2:
            self.is_buffed = True
            self.speed_multiplier = 1.5
        else:
            self.is_buffed = False
            self.speed_multiplier = 1.0

        # Mise à jour continue de la direction visuelle si le boss est visible (pour regarder le joueur)
        # je ne mets pas emerging car moche
        if self.phase in ["idle_pause", "charging"]:
            self._update_visual_direction()

        # 2. Gestion des timers de phase
        self.state_timer -= dt
        
        if self.phase == "emerging":
            self.is_invulnerable = False
            self._play_animation(dt, self._get_anim_list("sortie"), forward=True, loop=False)
            
            if self.state_timer <= 0:
                self.phase = "charging"
                self.state_timer = 1.5
                self.current_frame_index = 0
                sfx_charge = random.choice(["snd_charge_poseidon","snd_charge_poseidon2"])
                scene.sfx_manager.play(sfx_charge)

        elif self.phase == "charging":
            self._play_animation(dt, self._get_anim_list("idle"), forward=True, loop=True)
            
            if self.state_timer <= 0:
                self._execute_attack(scene)
                self.phase = "idle_pause"
                self.state_timer = 1.0 # self.pause
                self.current_frame_index = 0

        elif self.phase == "idle_pause":
            self._play_animation(dt, self._get_anim_list("idle"), forward=True, loop=True)

            if self.state_timer <= 0:
                # --- comportement aleatoire entre les attaques ---
                if self.current_attack == "multi":
                    # Apres un multi, c'est necessairement un solo (simple)
                    self.current_attack = "simple"
                else:
                    # Apres un solo, 1 chance sur 3 de refaire un solo (2/3 d'avoir un multi)
                    if random.random() < (1.0 / 3.0):
                        self.current_attack = "simple"
                    else:
                        self.current_attack = "multi"

                self.phase = "diving"
                self.state_timer = 1.0 
                self.is_invulnerable = True
                
                liste_sortie = self._get_anim_list("sortie")
                self.current_frame_index = max(0, len(liste_sortie) - 1)

        elif self.phase == "diving":
            self._play_animation(dt, self._get_anim_list("sortie"), forward=False, loop=False)
            
            if self.state_timer <= 0:
                self.phase = "hidden"
                self.hide()
                self.state_timer = random.uniform(0.5, 2.0)

        elif self.phase == "hidden":
            if self.state_timer <= 0:
                self._relocate()
                self.show()
                self.phase = "emerging"
                self.state_timer = 1.0
                self.current_frame_index = 0

        self.update_graphics()
        self.update_damage_state(dt)
        
        #self.try_hit_player(scene)

        self.update_buff_animation(dt)
        
        # 2. Surcharge specifique du comportement visuel du buff pour Poseidon (Gestion du Fondu)
        if hasattr(self, 'buff_item') and self.buff_item:
            if self.is_buffed:
                self.buff_item.setVisible(True)
                
                if self.phase == "emerging":
                    opacity = max(0.0, min(1.0, 1.0 - self.state_timer))
                    self.buff_item.setOpacity(opacity)
                    
                elif self.phase == "diving":
                    opacity = max(0.0, min(1.0, self.state_timer))
                    self.buff_item.setOpacity(opacity)
                    
                elif self.phase == "hidden":
                    self.buff_item.setOpacity(0.0)
                    
                else:
                    self.buff_item.setOpacity(1.0)
            else:
                self.buff_item.setOpacity(0.0)

    # --- LOGIQUE D'ATTAQUE ---

    def _execute_attack(self, scene):
        if self.current_attack == "simple":
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            
            # Choix de la direction cardinale dominante
            if abs(dx) > abs(dy):
                direction = "right" if dx > 0 else "left"
            else:
                direction = "down" if dy > 0 else "up"
            
            trident = Trident(source=self, direction=direction, damage=3, speed=12.0* self.speed_multiplier,target = self.target)
            trident.setPos(self.x + settings.tile_size / 2, self.y + settings.tile_size / 2)
            
            scene.addItem(trident)
            scene.projectiles.append(trident)
            
        elif self.current_attack == "multi":
            base_speed = 7 * self.speed_multiplier
            safe_col = random.randint(2, 14)
            
            for col in range(1, 15):
                if col == safe_col:
                    speed = base_speed / 1.4
                else:
                    speed = base_speed * random.uniform(0.9, 1.1)
                
                trident = Trident(source=self, direction="down", damage=1.5, speed=speed)
                
                spawn_x = col * settings.tile_size
                spawn_y = -2 * settings.tile_size + (HUD_HEIGHT * settings.tile_size)
                trident.x = spawn_x
                trident.y = spawn_y
                trident.setPos(spawn_x, spawn_y)
                
                scene.addItem(trident)
                scene.projectiles.append(trident)

    # --- LOGIQUE DE DEPLACEMENT / TELEPORTATION ---
    
    def _relocate(self):
        if self.current_attack == "simple":
            px, py = self.target.x, self.target.y
            offset_x = random.uniform(1, 4) * settings.tile_size * random.choice([-1, 1])
            offset_y = random.uniform(1, 4) * settings.tile_size * random.choice([-1, 1])
            new_x = px + offset_x
            new_y = py + offset_y
            
        else:
            new_x = random.uniform(4, 11) * settings.tile_size
            new_y = random.uniform(4, 7) * settings.tile_size

        self.x = new_x
        self.y = new_y

        self.setPos(self.x, self.y)

        self._update_visual_direction()

    # --- GESTION DES ANIMATIONS MANUELLES ---

    def _get_anim_list(self, action):
        """ Retourne la bonne liste de QPixmap selon l'action et la direction """
        if action == "idle":
            return self.anim_idle_up if self.visual_dir == "up" else self.anim_idle_down
        elif action == "sortie":
            return self.anim_sortie_up if self.visual_dir == "up" else self.anim_sortie_down

    def _play_animation(self, dt, frame_list, forward=True, loop=True):
        """ Gère la progression d'une liste de frames à 9 fps avec garde-fous anti-IndexError """
        if not frame_list:
            return

        self.anim_frame_timer += dt
        time_per_frame = 1.0 / self.fps
        
        if self.anim_frame_timer >= time_per_frame:
            self.anim_frame_timer -= time_per_frame
            
            if forward:
                self.current_frame_index += 1
                if self.current_frame_index >= len(frame_list):
                    self.current_frame_index = 0 if loop else len(frame_list) - 1
            else:
                self.current_frame_index -= 1
                if self.current_frame_index < 0:
                    self.current_frame_index = len(frame_list) - 1 if loop else 0
                    
        # --- GARDE-FOUS (CLAMP DE SECURITE CONTRE LES BRUSQUES CHANGEMENTS DE PHASES) ---
        if self.current_frame_index >= len(frame_list):
            self.current_frame_index = 0 if forward else len(frame_list) - 1
        if self.current_frame_index < 0:
            self.current_frame_index = len(frame_list) - 1 if not forward else 0
            
        self.setPixmap(frame_list[self.current_frame_index])
        
    # -- GESTION DE LA MORT ---
    
    
    def die(self):
        scene = self.scene()
        # Si on est deja en train de mourir, on ignore pour eviter les boucles
        if not scene or self.phase in ["dying_dialogue", "dying_dive", "dead"]:
            return
        
        self.is_damaged = False
        self.damage_timer = 0

        self.phase = "dying_dialogue"
        self.is_invulnerable = True
        self.kb_active = False
        self.is_stunned = False

        # 1. Detruire tous les tridents à l'ecran
        for p in list(scene.projectiles):
            if isinstance(p, Trident):
                p.die()

        # 2. Lancer le dialogue
        dialogues = [
            "* Nan je déconne, je parle français.",
            "* Tu te bats bien pour un humain, je dois le reconnaître. Je comprends pourquoi l'autre fou t'a fait confiance.",
            "* En revanche, tu es toujours très faible, surtout comparé à ce qui t'attend.",
            "* Si tu comptes réellement t'attaquer à la source du problème, eh bien je consens à te laisser passer.",
            "* Mais... sache que devant toi se dresse un ennemi redoutable.",
            "* Tung Tung Tung Sahur n'est qu'un pion dans son échiquier, l'homme à la tête de ça est bien plus fort qu'un simple général.",
            "* Écoute-moi bien, celui que tu cherches a déjà rameuté ses troupes dans le Sanctuaire du Nord.",
            "* Il y a bien longtemps, ce sanctuaire servait à prier les dieux (les vrais, pas moi).",
            "* Cependant, il a depuis longtemps été abandonné.",
            "* On y raconte que les dieux offraient à leurs adorateurs des pouvoirs hors du commun,",
            "et si cet homme a décidé de s'y rendre... c'est bien parce qu'il a une idée derrière la tête.",
            "* Prépare toutes tes forces, car le nom de cet homme est 'Emmanuel Macron' ! Le 25e président de la Ve République.",
            "* Cependant, j'ai foi en toi et je sais que tu peux le vaincre.",
            "* Tu as de la force dans tes petits bras, c'est pourquoi je vais te confier une arme.",
            "* Cette épée de pur tungstène est certes lourde mais extrêmement tranchante,",
            "et comme tu es goatesque, tu sauras la manier.",
            "* Marche en direction du nord et tu trouveras les montagnes sacrées.",
            "* Bonne chance mon enfant.."
        ]
        scene.dialogue_manager.start_text(dialogues)

        # 3. Changer la musique
        if hasattr(scene, "music_manager"):
            scene.music_manager.play("mus_truth")

        # Assurer que le boss est visible et regarde vers le bas pendant qu'il parle
        self.show()
        self.visual_dir = "down"
        self.current_frame_index = 0
        
    def _update_death_sequence(self, dt, scene):
        """ Gere la machine a etats de la mort. Retourne True si la sequence est en cours. """
        if self.phase == "dying_dialogue":
            # Animation d'idle pendant qu'il parle
            self._play_animation(dt, self._get_anim_list("idle"), forward=True, loop=True)
            self.update_graphics()
            
            # Attendre que le joueur ferme la boîte de dialogue
            if not scene.dialogue_manager.active:
                scene.session_flags["sword_tungsten"] = True
                
                self.phase = "dying_dive"
                self.state_timer = 1.0 # Durée de l'anim de plongée (9 frames)
                liste_sortie = self._get_anim_list("sortie")
                self.current_frame_index = max(0, len(liste_sortie) - 1)
                
                if self.target:
                    self.target.is_cinematic = True
                
            return True

        elif self.phase == "dying_dive":
            # Animation de plongée (reverse)
            self._play_animation(dt, self._get_anim_list("sortie"), forward=False, loop=False)
            self.update_graphics()
            
            # Fondu du buff s'il était actif
            if hasattr(self, 'buff_item') and self.buff_item:
                self.buff_item.setOpacity(max(0.0, min(1.0, self.state_timer)))
                
            self.state_timer -= dt
            
            # 5. La plongée est finie, on disparaît et on lance le fondu musical
            if self.state_timer <= 0:
                self.phase = "dead"
                self.hide()
                
                if hasattr(scene, "music_manager"):
                    # On force la durée à 2 secondes juste pour cette fois, puis on lance le fade_out
                    scene.music_manager.fade_out_duration = 0.1
                    scene.music_manager.start_fade_out()
                    
                if self.target:
                    self.target.is_cinematic = False
                    
                # On appelle le VRAI die() de la classe parente pour nettoyer l'entité et dropper le loot
                super().die()
                scene.sfx_manager.play("snd_sword_tungsten")
                if hasattr(scene, "player"):
                    scene.player.obtain_item("sword_tungsten",duration=4.5)
                    
                    QTimer.singleShot(5000, scene.start_room_music) #5 secondes

                
            return True
            
        elif self.phase == "dead":
            return True

        # Si on n'est pas en train de mourir, on retourne False
        return False
    