# -*- coding: utf-8 -*
from game import screen_manager
from game import screen_manager
from game import screen_manager
from game import screen_manager
from PyQt5 import sip
import math
import random
from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QRectF

from game.enemies.enemy import Enemy
from game.config import BASE_TILE_SIZE, HUD_HEIGHT, GRID_WIDTH, GRID_HEIGHT
from game.settings import settings
from game.animspr import load_animation_sequence

from game.enemies.placeholder1 import Placeholder1
from game.enemies.arakwa import Arakwa

from PyQt5.QtCore import QTimer



class Tungtungsahur(Enemy):
    """Boss Tung Tung Sahur : combat de charges, sauts de zone et invocations."""
    def __init__(self, scale, x, y):
        self._x = 0
        self._y = 0
        
        super().__init__(scale, x, y)

        # --- STATS DE BASE ---
        self._pv_max = 20
        self.pv_main = self._pv_max
        self.aggro_range = settings.tile_size * 16
        self.speed = 0
        self.use_pathfinding = False # On désactive l'A* de l'ennemi standard
        self.loot = []

        # degats de l'ennemi
        self.damage = 1              # dégâts de la charge
        self.aoe_damage = 1.5        # dégâts du zone_jump
        
        # --- ENRAGED / BUFF STATE ---
        self.speed_multiplier = 1.0
        
        base_path = "assets/enemies/tungtungsahur/"
        self.taille_boss = (1,2)
        self.death_cry ="snd_tuntun"


        # chargement des sprites 

        ts = settings.tile_size
        w = self.taille_boss[0] * ts
        h = self.taille_boss[1] * ts
        self.spr_idle     = QPixmap(f"{base_path}tungtungsahur_idle.png").scaled(w, h, transformMode=Qt.FastTransformation)
        self.spr_prejump  = QPixmap(f"{base_path}tungtungsahur_pre_jump.png").scaled(w, h, transformMode=Qt.FastTransformation)
        # 4 frames de charge
        self.anim_charge = []
        for i in range(1, 5):
            px = QPixmap(f"{base_path}tungtungsahur{i}.png").scaled(w, h, transformMode=Qt.FastTransformation)
            self.anim_charge.append(px)
        # 10 frames de mort (sortie)
        self.anim_sortie = load_animation_sequence(f"{base_path}tungtungsahur_sortie", self.taille_boss, 10)

        # --- MACHINE A ETATS & PATTERNS ---
        self.fps = 9.0
        self.anim_frame_timer = 0.0
        self.current_frame_index = 0
        
        # Etats possibles: 
        # "idle_menace", "pre_charge", "charging", "recovery", "spawn_summon", "dying_dialogue", "dying_fall", "dead"
        self.phase = "idle_menace" 
        self.state_timer = 1.0 # 9 frames / 9 fps = 1 seconde pour la sortie initiale
        
        # charge ou zone_jump
        self.current_attack = "charge" 
        self.is_invulnerable = False

        # variables pour l'attaque charge 
        self.charge_dir_x = 0.0          # vecteur normalisé de la charge
        self.charge_dir_y = 0.0
        self.charge_speed = 0.0          # vitesse actuelle (utilisée aussi pour le glide)
        self.charge_max_speed = settings.tile_size * 24
        self.charge_timer = 0.0          # safety timeout
        # variables pour l'attaque jump
        self.charge_target_x = 0.0      # position verrouillée en pre_charge
        self.charge_target_y = 0.0
        self.jump_elapsed = 0.0
        self.jump_duration = 0.55
        self.jump_start_x = 0.0
        self.jump_start_y = 0.0
        self.zone_marker = None          # QGraphicsEllipseItem au sol pour marquer la zone
        # spawn de mobs pour la phase 2
        self.cycle_count = 0             # nb de cycles recovery depuis dernier spawn
        self.speed_multiplier = 1.0
        
        self.sfx_cooldown = 0.0
            
        # Initialisation sur la première frame de sortie
        self.setPos(self.x, self.y)
        if self.anim_sortie:
            self.setPixmap(self.anim_sortie[0])
    
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        min_x = 1 * settings.tile_size
        max_x = 14 * settings.tile_size
        self._x = max(min_x, min(value, max_x))

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        min_y = (1+HUD_HEIGHT) * settings.tile_size
        max_y = (9+HUD_HEIGHT) * settings.tile_size
        self._y = max(min_y, min(value, max_y))

    def _update_visual_direction(self):
        """Adapte la direction visuelle si le joueur l'a completement depasse."""
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
        """Intercepte les textures d'animations pour appliquer les effets visuels a la volee."""
        if not pixmap or pixmap.isNull():
            super().setPixmap(pixmap)
            return
        
        if hasattr(self, 'phase') and self.phase in ["dying_dialogue", "dying_fall"]:
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
        """Surcharge essentielle : empeche la classe parente d'ecraser le pixmap."""
        pass

    def update(self, dt, scene):
        # sert a rien, on fait ça avec musique de room -> fait des bugs sinon
        # if not getattr(self, "_music_started", False):
        #     self._music_started = True
        #     if hasattr(scene, "music_manager"):
        #         scene.music_manager.play("mus_mini_boss", fade_in=1)
                
        if self._update_death_sequence(dt, scene):
            return
        
        if self.sfx_cooldown > 0:
            self.sfx_cooldown -= dt
            
        # 1. Gerer les états bloquants (Stun, Knockback) s'il est vulnerable
        if not self.is_invulnerable:
            if self.kb_active:
                self.apply_knockback(dt, scene)
                self.update_graphics()
                self.update_damage_state(dt)
                return

        if not self.target:
            return
        
        # gestion de buff mi-vie (enraged)
        if self.pv_main <= int(2*self._pv_max / 3):
            if not self.is_buffed:       # premier passage en P2
                self.cycle_count = 0     # reset le compteur
            self.is_buffed = True
            self.speed_multiplier = 1.5
        else:
            self.is_buffed = False
            self.speed_multiplier = 1.0

        # Mise à jour continue de la direction visuelle si le boss est visible (pour regarder le joueur)
        self.state_timer -= dt
        if self.phase == "idle_menace":
            self._update_idle_menace(dt, scene)
        elif self.phase == "pre_charge":
            self._update_pre_charge(dt, scene)
        elif self.phase == "charging":
            self._update_charging(dt, scene)
        elif self.phase == "recovery":
            self._update_recovery(dt, scene)
        elif self.phase == "spawn_summon":
            self._update_spawn_summon(dt, scene)
        self.update_graphics()
        self.update_damage_state(dt)
        
            # if self.phase in ["idle_pause", "charging"]:
        #     self._update_visual_direction()

    # Differentes methodes des comportments:

    def _update_idle_menace(self, dt, scene):
        """Gere la phase d'attente menacante."""
        self.setPixmap(self.spr_idle)
        self.is_invulnerable = False
        if self.state_timer<=0:
            if random.random()<0.67:
                self.current_attack = "charge"
            else : 
                self.current_attack = "zone_jump"
            self.phase = "pre_charge"
            self.state_timer = 0.67/2


    def _update_pre_charge(self, dt, scene):
        """Gere la phase de preparation de charge ou de saut."""
        self.setPixmap(self.spr_prejump)
        self.is_invulnerable = True
        
        # au premier tick de la precharge, 
        # verrouille la position de l'ennemi + lance le son

        if not getattr(self, "_pre_charge_initialized", False):
            self._pre_charge_initialized = True
            if self.sfx_cooldown <= 0:
                scene.sfx_manager.play("snd_tuntun")
                self.sfx_cooldown = 3.0

            px,py = self.target.get_center()

            if self.current_attack == "charge":
                

                dx = px - self.x
                dy = py - self.y

                dist = math.hypot(dx,dy)

                if dist > 0:
                    self.charge_dir_x = dx/dist
                    self.charge_dir_y = dy/dist
                else:
                    self.charge_dir_x = 1.0
                    self.charge_dir_y = 0.0

                # cible = position du joueur + depassement 
                # de tile

                overshoot = 2.5 * settings.tile_size
                self.charge_target_x = px + self.charge_dir_x * overshoot
                self.charge_target_y = py + self.charge_dir_y * overshoot
                self.charge_speed = self.charge_max_speed * self.speed_multiplier

                self.charge_timer = 0.0

            else: #jump zone
                self.charge_target_x = px
                self.charge_target_y = py
                self.jump_start_x = self.x
                self.jump_start_y = self.y
                self.jump_elapsed = 0.0

                self._create_zone_marker(scene,px,py)

        ts = settings.tile_size
        # Clamper la cible dans les mêmes limites que les setters x/y
        self.charge_target_x = max(ts, min(self.charge_target_x, (16 - self.taille_boss[0]) * ts))
        self.charge_target_y = max((1 + HUD_HEIGHT) * ts, min(self.charge_target_y, (9 + HUD_HEIGHT) * ts))


        if self.state_timer <= 0:
            self._pre_charge_initialized = False
            self.phase = "charging"
            self.current_frame_index = 0
            self.anim_frame_timer = 0.0


            

    def _update_charging(self, dt, scene):
        """Gere le mouvement de charge et les collisions."""
        if self.current_attack == "charge":
            self._play_animation_list(dt,self.anim_charge, loop = True)

            # charge droit sur le joueur avec depassement
            
            self.x+= self.charge_dir_x *self.charge_speed * dt
            self.y+= self.charge_dir_y *self.charge_speed * dt

            self.setPos(self.x,self.y)

            self.charge_timer +=dt

            self._check_charge_hit(scene)

            # condition de fin

            dx = self.charge_target_x - self.x
            dy = self.charge_target_y - self.y
            dist_to_target = math.hypot(dx,dy)
            
            if dist_to_target < settings.tile_size * 0.3 or self.charge_timer>0.8:
                self._enter_recovery(scene)

        else : # jump zone
            self.jump_elapsed += dt
            p = min(self.jump_elapsed/self.jump_duration, 1.0)

            # Interpoler les CENTRES (pas les coins)
            start_cx = self.jump_start_x + settings.tile_size * 0.5
            start_cy = self.jump_start_y + settings.tile_size
            end_cx   = self.charge_target_x
            end_cy   = self.charge_target_y
            cx = start_cx + (end_cx - start_cx) * p
            cy = start_cy + (end_cy - start_cy) * p
            cy -= math.sin(p * math.pi) * settings.tile_size * 2.5
            # Repositionner le sprite (coin haut-gauche = centre - demi-taille)
            self.x = cx - settings.tile_size * 0.5
            self.y = cy - settings.tile_size
            
            self.setPos(self.x,self.y)

            self.setPixmap(self.spr_idle)

            if p>=1.0:
                self._on_zone_jump_land(scene)
                self._enter_recovery(scene)




    def _update_recovery(self, dt, scene):
        """Gere la deceleration post-charge (glide) et la transition de phase."""
        self.setPixmap(self.spr_idle)
        self.is_invulnerable = False

        #  glide : deceleration prograssive du boss si en mouvement

        if self.charge_speed > settings.tile_size * 0.5:
            self.charge_speed *= (1-8*dt)
            self.x += self.charge_dir_x * self.charge_speed * dt
            self.y += self.charge_dir_y * self.charge_speed * dt
            self.setPos(self.x,self.y)
        else:
            self.charge_speed = 0.0

        if self.state_timer <= 0:

            self.cycle_count += 1


        # phase 2
            if self.is_buffed and self.cycle_count >= 3:
                self.cycle_count = 0
                self.phase = "spawn_summon"
                self.state_timer = 1.0
            else:
                self.phase = "idle_menace"
                self.state_timer = 1.0
            

    def _update_spawn_summon(self, dt, scene):
        """Gere l'invocation d'ennemis sbires en phase 2."""
        self.setPixmap(self.spr_idle)
        self.is_invulnerable = True

        if not getattr(self, "_summon_done", False):
            self._summon_done = True
            scene.sfx_manager.play("snd_tuntun2")
            self._spawn_minions(scene)

        if self.state_timer<=0:
            self._summon_done = False
            self.phase = "idle_menace"
            self.state_timer = 1.0

    def _play_animation_list(self, dt, frame_list, loop=True):
        """Joue une sequence d'animation a vitesse fixe."""
        # Avance dans une liste de frames à self.fps
        if not frame_list:
            return
        self.anim_frame_timer += dt
        tpf = 1.0 / self.fps
        if self.anim_frame_timer >= tpf:
            self.anim_frame_timer -= tpf
            self.current_frame_index += 1
            if self.current_frame_index >= len(frame_list):
                self.current_frame_index = 0 if loop else len(frame_list) - 1
        idx = max(0, min(self.current_frame_index, len(frame_list) - 1))
        self.setPixmap(frame_list[idx])
        
#  Utilitaires

    def _enter_recovery(self, scene):
        """Passe le boss en phase de recuperation."""
        self.phase = "recovery"
        self.state_timer = 0.5
        self.current_frame_index = 0


    def _check_charge_hit(self,scene):
        """Verifie si la charge touche le joueur et inflige des degats."""
        #  inglige des degats au joueur si la hitbox
        # touche le joueur pdt la charge
        bx = self.x
        by = self.y
        bw = self.taille_boss[0] * settings.tile_size
        bh = self.taille_boss[1] * settings.tile_size

        boss_rect = QRectF(bx,by,bw,bh)

        px,py,pw,ph = scene.player.get_hitbox()

        player_rect = QRectF(px,py,pw,ph)

        if boss_rect.intersects(player_rect):
            scene.player.take_damage(scene, self.damage, self)
            # scene.player.knockback(self.x,self.y,16)


    def _create_zone_marker(self,scene,center_x,center_y):
        """Cree un marqueur visuel au sol pour l'attaque de saut de zone."""
        # faire le marker pour le jump zone pr indiquer le joueur
        ts = settings.tile_size
        marker = QGraphicsEllipseItem(
            center_x-ts*1.5,
            center_y-ts*1.5,
            ts*3,
            ts*3
        )
        marker.setPen(QPen(QColor(220, 50, 50, 200), 2))
        marker.setBrush(QBrush(QColor(200, 0, 0, 60)))
        marker.setZValue(5)
        scene.addItem(marker)
        self.zone_marker = marker
        
        
    def _on_zone_jump_land(self, scene):
        """Gere l'atterrissage du saut et declenche les degats de zone."""
        # supprime le marker et fait l'AOE
        if self.zone_marker and self.zone_marker.scene():
            scene.removeItem(self.zone_marker)
            self.zone_marker = None
        
        if self.sfx_cooldown <= 0:
                scene.sfx_manager.play("snd_tuntun")
                self.sfx_cooldown = 3.0

        target_col = int(self.charge_target_x // settings.tile_size)
        target_row = int((self.charge_target_y - HUD_HEIGHT * settings.tile_size) // settings.tile_size)

        self._apply_zone_damage(scene,target_col,target_row)

    def _apply_zone_damage(self, scene, center_col, center_row):
        """Inflige des degats de zone (3x3 tuiles) au joueur."""
        # inflige des dgts si le joueur est dans la zone 3*3
        px,py,pw,ph =  scene.player.get_hitbox()
        player_rect = QRectF(px,py,pw,ph)
        ts = settings.tile_size
        for dc in [-1,0,1]:
            for dr in [-1,0,1]:
                col = center_col + dc
                row = center_row + dr
                if col<0 or col>GRID_WIDTH or row<0 or row>GRID_HEIGHT:
                    continue
                tile_rect = QRectF(col*ts, (row+HUD_HEIGHT)*ts,ts,ts)
                
                if tile_rect.intersects(player_rect):
                    scene.player.take_damage(scene, self.aoe_damage, self)
                    return
                
    def _spawn_minions(self, scene):
        """Fait apparaitre des ennemis secondaires autour du boss."""
        ts = settings.tile_size
        min_x = 1 * ts
        max_x = (GRID_WIDTH-2) * ts
        min_y = (1 + HUD_HEIGHT) * ts
        max_y = (9 + HUD_HEIGHT) * ts
        
        EnemyClass = random.choice([Placeholder1, Arakwa])
        ox = random.choice([-1, 1]) * random.uniform(2, 4) * ts
        oy = random.choice([-1, 1]) * random.uniform(2, 4) * ts
        spawns = [(EnemyClass, ox, oy)]
        
        for EnemyClass, ox, oy in spawns:
            spawn_x = max(min_x, min(self.x + ox, max_x))
            spawn_y = max(min_y, min(self.y + oy, max_y))
            e = EnemyClass(settings.scale, spawn_x, spawn_y)
            e.room_name = getattr(self, 'room_name', None)
            e.enemy_id = None

            e.set_target(scene.player)
            
            scene.enemies.append(e)
            scene.addItem(e)

        
    # -- GESTION DE LA MORT ---
    
    
    def die(self):
        """Gere la mort du boss (dialogues, chute, musique)."""
        scene = self.scene()
        # Si on est deja en train de mourir, on ignore pour eviter les boucles
        if not scene or self.phase in ["dying_dialogue", "dying_fall", "dead"]:
            return
        
        self.is_damaged = False
        self.damage_timer = 0

        self.phase = "dying_dialogue"
        self.is_invulnerable = True
        self.kb_active = False
        self.is_stunned = False

        # supprimer le marker si il est encore là
        if self.zone_marker and self.zone_marker.scene():
            scene.removeItem(self.zone_marker)
            self.zone_marker = None

        # Supprimer tous les mobs encore en vie dans la salle
        for enemy in scene.enemies[:]:   # copie de la liste pour itérer sans bug
            if enemy is self:
                continue
            if enemy.scene():
                scene.removeItem(enemy)
            scene.enemies.remove(enemy)

        # Lancer le dialogue
        dialogues = [
            "* Tung tung tung",
            "* Tung tung tung",
            "* Tung tung tung",
            "* Tung tung tung sahur",
            "* Nan je déconne, je parle français.",
            "* Tu as peut-être réussi à m'avoir,",
            "* Mais sache que... tu...",
            "* Tu es encore loin de pouvoir rivaliser avec lui...",
            "* Mon maître qui domine ce monde,",
            "* Celui qui règne sans merci au-delà des terres et des mers.",
            "* Inutile de te révéler son nom...",
            "* Tu l'apprendras bien assez vite...",
            "* All... Hail... Em... *meurt*"
        ]
        scene.dialogue_manager.start_text(dialogues,"font4")

        # 3. Changer la musique
        if hasattr(scene, "music_manager"):
            scene.music_manager.player.setLoopCount(1)
            scene.music_manager.play("mus_tung_vaincu")

        # Assurer que le boss est visible et regarde vers le bas pendant qu'il parle
        self.show()
        # self.visual_dir = "down"
        self.current_frame_index = 0
        
    def _update_death_sequence(self, dt, scene):
        """Gere la sequence de mort (dialogue puis chute)."""
        if self.phase == "dying_dialogue":
            # Animation d'idle pendant qu'il parle
            # self._play_animation(dt, self._get_anim_list("idle"), forward=True, loop=True)
            self.setPixmap(self.spr_idle)
            self.update_graphics()
            
            # Attendre que le joueur ferme la boîte de dialogue
            if not scene.dialogue_manager.active:
                
                self.phase = "dying_fall"
                self.state_timer = 1.0
                self.current_frame_index = 0
                
                if self.target:
                    self.target.is_cinematic = True
                
            return True

        elif self.phase == "dying_fall":
            # animation de chute du triple T
            self._play_animation_list(dt, self.anim_sortie, loop=False)
            self.update_graphics()
            self.state_timer -= dt
            
            
            # 5. La plongée est finie, on disparaît et on lance le fondu musical
            if self.state_timer <= 0:
                self.phase = "dead"
                self.hide()
                scene.session_flags["tung_vaincu"] = True
                scene.current_save.data["flags"]["tung_vaincu"] = True

                # flag composite si shiny est mort aussi
                if scene.get_flag("shiny_dead"):
                    scene.session_flags["shiny_et_tung_dead"] = True
                    if scene.get_flag("mayor_spoke_first"):
                        scene.session_flags["shiny_tung_dead_spoke"] = True
                # flag composite tung mort + déjà parlé au maire
                if scene.get_flag("mayor_spoke_first"):
                    scene.session_flags["tung_vaincu_spoke"] = True
                
                if hasattr(scene, "music_manager"):
                    scene.music_manager.player.setLoopCount(-2)
                    scene.start_room_music()
                    if self.target:
                        self.target.is_cinematic = False
                    
                self.trigger_jesus_spawn(scene)
                    
                super().die()
                
            return True
            
        elif self.phase == "dead":
            return True

        # Si on n'est pas en train de mourir, on retourne False
        return False

    def trigger_jesus_spawn(self, scene):
        """Declenche l'apparition de Jesus apres la defaite."""
        scene.session_flags["spawn_jesus"] = True
        scene.check_pending_npcs()

    
