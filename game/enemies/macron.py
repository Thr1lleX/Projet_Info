# -*- coding: utf-8 -*-
import math
import random
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer

from game.enemies.enemy import Enemy
from game.config import HUD_HEIGHT, GRID_WIDTH, GRID_HEIGHT, DEBUG, BASE_TILE_SIZE
from game.settings import settings
from game.animspr import load_animation_sequence
from game.attacks.macron_attaques import ProjectGrenade, GrenadeMacron, DalleLumineuse


class Macron(Enemy):
    def __init__(self, scale, x, y):
        # Initialise les attributs du boss, ses points de vie, ses animations et ses repliques de dialogue
        self._x = 8 * settings.tile_size
        self._y = 0
        
        super().__init__(scale, self._x, self._y)

        self._pv_max = 150
        self.pv_main = self._pv_max
        self.speed = 0 
        self.use_pathfinding = False 
        self.knockback = 0
        
        self.hitbox_width = settings.tile_size
        self.hitbox_height = settings.tile_size
        self.taille_boss = (1, 1)
        self.death_cry = "snd_2efois"
        
        self.damage_duration = 0.10

        self.frames = load_animation_sequence("assets/enemies/macron/macron", (1, 1), 14)
        self.setPixmap(self.frames[0])
        self.current_frame = 0
        self.anim_timer = 0.0
        
        self.global_time = 0.0
        
        self.phase = -1
        self.attack_state = "idle"
        self.attack_timer = 0.0
        self.grenades_to_drop = 0
        self.grenade_target_pos = None
        self.dalles_active = []
        self.grenades_active = []
        self.tiles_id_0 = []
        
        # Gestion automatique des répliques
        self.dialogue_lines = []
        self.dialogue_timer = 0.0
        self.duration_per_line = 0.0
        self.current_line_idx = -1
        self.is_dialogue_active = False

        self.dialogue_intro = ["* Emmanuel Macron, j'espère que vous allez bien.", 
                               "* Je vois que tu m'as explosé le bras droit, j'espère que tu es fière.", 
                               "* Cependant, j'ai bientôt acquis les pouvoirs divins.", 
                               "* Une fois que cela sera fait, tu ne pourras plus rien faire contre moi.",
                               "* Des femmes et des hommes, des enfants et des familles, des vies entières mourront.",
                               "* Penses-tu pouvoir me stopper ?"]
        
        self.dialogue_mid_fight = ["*Nghh*", 
                                   "* Je crois que tu ne réalises pas encore l'ampleur de mon plan.",
                                   "* Grâce à mes nouveaux pouvoirs, je règnerai en maître sur le monde.",
                                   "* Je pourrai agir directement sur l'esprit des foules. Il me suffira d'un vecteur approprié.",
                                   "* Faites-vous vacciner !",
                                   "* Et bien sûr, tout le monde m'obéira.",
                                   "* PARCE QUE C'EST NOTRE PROJET !",
                                   "* Aussi longtemps que ce combat devra durer, nous le mènerons, sans faiblir."
                                   ]
        self.dialogue_mort = ["*Arrgh*",
                              "* Qui aurait pu prédire ? J'ai mal évalué mon adversaire.", 
                              "* Mais ne te pense pas vainqueur pour ça.", 
                              "* Je reviendrai, sois-en sûr.",
                              "* Mon corps ne périra pas face à de simples coups d'épée."]
        
        self.dialogue_vivant = ["*Arrgh*", 
                                "* Je vois que je ne peux pas te vaincre, mais...", 
                                "* Ne pense pas t'en sortir, si je dois y passer, toi aussi",
                                "* Tu n'as pas été assez rapide...", 
                                "* J'ai encore assez d'énergie pour tous nous faire péter !"]

        self.is_exploding = False
        self.explosion_frames = []
        self.explosion_frame_idx = 0
        self.explosion_timer = 0.0
        
        self.last_attack = None
        self.current_attack = None
        self.attack_cooldown = 0.0

    def setPixmap(self, pixmap):
        # Applique le pixmap en ajoutant une teinte rouge si blesse ou blanche clignotante si invulnerable
        if not pixmap or pixmap.isNull():
            super().setPixmap(pixmap)
            return

        if getattr(self, "is_damaged", False):
            tinted = pixmap.copy()
            painter = QPainter(tinted)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(tinted.rect(), QColor(255, 0, 0, 140))
            painter.end()
            super().setPixmap(tinted)
            return

        if getattr(self, "is_invulnerable", False):
            if int(getattr(self, "blink_timer", 0) * 15) % 2 == 0:
                tinted = pixmap.copy()
                painter = QPainter(tinted)
                painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
                painter.fillRect(tinted.rect(), QColor(255, 255, 255, 140))
                painter.end()
                super().setPixmap(tinted)
                return

        super().setPixmap(pixmap)

    def init_fight(self, scene):
        """ Configuration et blocages initiaux """
        inventory = scene.screen_manager.inventory
        inventory._equipped_item_id = None
        scene.screen_manager.pause_blocked = True
        scene.screen_manager.inventory_blocked = True
        scene.screen_manager.interact_blocked = True
        scene.screen_manager.item_blocked = True
        
        # Extraction des cases vides depuis la vraie matrice de la salle
        self.tiles_id_0 = []
        if hasattr(scene, 'room_data') and "tiles" in scene.room_data:
            grid = scene.room_data["tiles"]
            for row in range(len(grid)):
                for col in range(len(grid[row])):
                    # On cible uniquement le sol pur sans rien par-dessus + bas de salle
                    if grid[row][col] == 0 or (col, row) in [(7, 10), (8, 10)]:
                        self.tiles_id_0.append((col * settings.tile_size, (row + HUD_HEIGHT) * settings.tile_size))

    def setup_auto_dialogue(self, scene, lines, total_duration):
        """ Calcule et prepare le DialogueManager pour defiler automatiquement """
        self.dialogue_lines = lines
        self.duration_per_line = total_duration / len(lines)
        self.current_line_idx = 0
        self.dialogue_timer = 0.0
        self.is_dialogue_active = True
        
        # On force le DialogueManager à démarrer sur la première réplique
        if hasattr(scene, "dialogue_manager"):
            scene.dialogue_manager.start_text(self.dialogue_lines[0])

    def update_auto_dialogue(self, dt, scene):
        """ Gere le passage automatique de ligne en ligne sans bloquer l'update globale """
        if not self.is_dialogue_active or not hasattr(scene, "dialogue_manager"):
            return

        self.dialogue_timer += dt
        if self.dialogue_timer >= self.duration_per_line:
            self.dialogue_timer = 0.0
            self.current_line_idx += 1
            
            if self.current_line_idx < len(self.dialogue_lines):
                # On réinjecte le texte directement pour écraser la ligne précédente
                scene.dialogue_manager.start_text(self.dialogue_lines[self.current_line_idx])
                
                # Evenement specifique : Son a la 3eme ligne (index 2) de la phase 0
                if self.phase == 0 and self.current_line_idx == 4:
                    if hasattr(scene, 'sfx_manager'): 
                        scene.sfx_manager.play("snd_femmes_et_hommes")
                if self.phase == 3 and self.current_line_idx == 4:
                    if hasattr(scene, 'sfx_manager'): 
                        scene.sfx_manager.play("snd_macron_vaccin")
                if self.phase == 3 and self.current_line_idx == 5:
                    if hasattr(scene, 'sfx_manager'): 
                        scene.sfx_manager.play("snd_macron_for_sure")
                if self.phase == 3 and self.current_line_idx == 6:
                    if hasattr(scene, 'sfx_manager'): 
                        scene.sfx_manager.play("snd_macron_projet")
                if self.phase == 3 and self.current_line_idx == 7:
                    if hasattr(scene, 'sfx_manager'): 
                        scene.sfx_manager.play("snd_long_macron")
                if self.phase == 6 and self.pv_main <= 0 and self.current_line_idx == 1:
                    if hasattr(scene, 'sfx_manager'): 
                        scene.sfx_manager.play("snd_macron_predire")
            else:
                scene.dialogue_manager.close()
                self.is_dialogue_active = False

    def take_damage(self, scene, damage, source=None):
		   
        """ override de take_damage pour ne pas le tuer si atteint 0 pv """
		   
        if self.is_invulnerable or getattr(self, 'is_exploding', False):
            return
            
        self.pv_main -= damage
        self.is_damaged = True
        self.damage_timer = 0.0
        self.damage_duration = 0.1
        
        self.is_invulnerable = True
        self.invuln_timer = 0
    
        
        if self.frames:
            self.setPixmap(self.frames[self.current_frame])
        
        if DEBUG:
            class_name = self.__class__.__name__
            print(f"[{class_name.upper()} HP] : {self.pv_main}/{self._pv_max}")
        
        # S'il descend a 0 ou moins, on le bloque a 0 pour le combat
        if self.pv_main <= 0:
            self.pv_main = 0
            # IMPORTANT: On ne declenche PAS super().take_damage() pour eviter sa mort immediate !


    def update(self, dt, scene):
        # Gere le cycle de vie du boss a chaque frame (animations, phases du combat, chronologie et dialogues)
        if not self.is_invulnerable:
            if self.kb_active:
                self.apply_knockback(dt, scene)
                self.setPixmap(self.frames[self.current_frame])
                self.update_graphics()
                self.update_damage_state(dt)
                return
            
        if self.is_exploding:
            self.update_explosion(dt, scene)
            return True

        # Animation visuelle (100ms)
        self.anim_timer += dt
        if self.anim_timer >= 0.1:
            self.anim_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.setPixmap(self.frames[self.current_frame])
            
                
        if getattr(self, "is_invulnerable", False):
            self.invuln_timer -= dt
            self.blink_timer = getattr(self, "blink_timer", 0) + dt
            if self.invuln_timer <= 0:
                self.is_invulnerable = False

        # Chronologie globale liee a la musique
        self.global_time += dt

        # Initialisation du combat
        if self.phase == -1:
            self.init_fight(scene)
            self.phase = 0
            if hasattr(scene, 'sfx_manager'): scene.sfx_manager.play("snd_macron")
            self.setup_auto_dialogue(scene, self.dialogue_intro, 39.5)

        # Update des entites independantes
        for dalle in self.dalles_active[:]:
            if dalle.update(dt, scene, self):
                self.dalles_active.remove(dalle)

        for gren in self.grenades_active[:]:
            gren.update(dt, scene)
            if gren.fuse_timer <= 0:
                self.grenades_active.remove(gren)

        # --- Phase 0 : Intro ---
        if self.global_time < 39.5:
            self.update_auto_dialogue(dt, scene)

        # --- Slide ---
        elif self.global_time < 43.5:
            if self.phase == 0:
                self.phase = 0.5
                if hasattr(scene, 'sfx_manager'): scene.sfx_manager.play("snd_guerre")
                if hasattr(scene, "dialogue_manager"): scene.dialogue_manager.close()
                self.is_dialogue_active = False
                
            progress = (self.global_time - 39.5) / 4.0
            target_y = (4 + HUD_HEIGHT) * settings.tile_size
            self.y = 0 + target_y * progress
            self.setPos(self.x, self.y)

        # --- Phase 1 : Attaques Normales ---
        elif self.global_time < 137.0: 
            if self.phase == 0.5:
                self.phase = 1
                self.attack_state = "choose_attack"
            self.update_attacks(dt, scene, is_final_phase=False)

        # --- Phase 2 : Repositionnement ---
        elif self.global_time < 140.0:
            self.x = 8 * settings.tile_size
            self.y = (4 + HUD_HEIGHT) * settings.tile_size
            self.setPos(self.x, self.y)
            if self.phase == 1:
                self.phase = 2

        # --- Phase 3 : Dialogue Echec ---
        elif self.global_time < 175.05:
            if self.phase == 2:
                self.phase = 3
                if hasattr(scene, 'sfx_manager'): scene.sfx_manager.play("snd_macron_echec")
                self.setup_auto_dialogue(scene, self.dialogue_mid_fight, 35.05)
            
            self.update_auto_dialogue(dt, scene)
            

        # --- Phase Finale : Attaques Boostees ---
        elif self.global_time < 219.05: 
            if self.phase == 3:
                self.phase = 4
                if hasattr(scene, "dialogue_manager"): scene.dialogue_manager.close()
                self.is_dialogue_active = False
                self.attack_state = "choose_attack"
            self.update_attacks(dt, scene, is_final_phase=True)

        # --- Phase Remplacement Fin ---
        elif self.global_time < 230.04: 
            self.x = 8 * settings.tile_size
            self.y = (4 + HUD_HEIGHT) * settings.tile_size
            self.setPos(self.x, self.y)
            if self.phase == 4:
                self.phase = 5

        # --- Fin du combat et Choix des branches ---
        else:
            if self.phase == 5:
                self.phase = 6
                if self.pv_main <= 0:
                    self.setup_auto_dialogue(scene, self.dialogue_mort, 13.96)
                else:
                    self.setup_auto_dialogue(scene, self.dialogue_vivant, 13.96)

            self.update_auto_dialogue(dt, scene)
            
            # Fin absolue du timer (a 4:04 soit 244 secondes)
            if self.global_time >= 244.0: 
                if self.phase == 6:
                    self.phase = 7
                    if hasattr(scene, "dialogue_manager"): scene.dialogue_manager.close()
                    self.trigger_end_sequence(scene)

        self.update_graphics()
        self.update_damage_state(dt)

    def update_attacks(self, dt, scene, is_final_phase):
        # Gere l'arbre de decision et l'execution des attaques (grenades et dalles lumineuses)
        if self.attack_state == "choose_attack":
            self.attack_cooldown -= dt
            if self.attack_cooldown > 0:
                return
        
            if self.last_attack == "dalles":
                self.attack_state = "grenades"
        
            elif self.last_attack == "grenades":
                self.attack_state = random.choices(["dalles", "grenades"], weights=[5, 1])[0]
        
            else:
                # Premiere attaque du combat
                self.attack_state = random.choice(["dalles", "grenades"])
        
            self.attack_timer = 0.0

        elif self.attack_state == "dalles":
            self.current_attack = "dalles"
            self.attack_timer += dt
            if self.attack_timer < 0.5:
                tx = 8 * settings.tile_size
                ty = (4 + HUD_HEIGHT) * settings.tile_size
                self.x += (tx - self.x) * (dt / 0.5)
                self.y += (ty - self.y) * (dt / 0.5)
                self.setPos(self.x, self.y)
            else:
                ratio = 0.5 if is_final_phase else 0.75
                blink_dur = 0.75 if is_final_phase else 2.0
                num_dalles = int(len(self.tiles_id_0) * ratio)
                chosen = random.sample(self.tiles_id_0, num_dalles)
                
                for i, pos in enumerate(chosen):
                    dalle = DalleLumineuse(pos[0], pos[1], blink_dur, 3.0, play_sound=(i==0))
                    scene.addItem(dalle)
                    self.dalles_active.append(dalle)
                
                self.attack_state = "wait_attack"
                self.attack_timer = blink_dur + 3.5

        elif self.attack_state == "grenades":
            if self.grenades_to_drop == 0:
                self.grenades_to_drop = 8 if is_final_phase else 4
                self.grenade_targets = random.sample(self.tiles_id_0, self.grenades_to_drop)
                scene.sfx_manager.play("snd_grenade")
                self.attack_state = "move_grenade"
                self.attack_timer = 0.0

        elif self.attack_state == "move_grenade":
            self.attack_timer += dt
            if not self.grenade_targets:
                self.grenades_to_drop = 0
                self.attack_state = "wait_attack"
                self.attack_timer = 3.0
                return

            target = self.grenade_targets[0]
            if self.attack_timer < 0.5:
                self.x += (target[0] - self.x) * (dt / 0.5)
                self.y += (target[1] - self.y) * (dt / 0.5)
                self.setPos(self.x, self.y)
            else:
                self.x, self.y = target
                self.setPos(self.x, self.y)
                gren = GrenadeMacron(self, self.x, self.y)
                scene.addItem(gren)
                self.grenades_active.append(gren)
                if hasattr(scene, 'sfx_manager'): scene.sfx_manager.play("snd_macron_explosion")
                
                self.grenade_targets.pop(0)
                self.attack_timer = 0.0

        elif self.attack_state == "wait_attack":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "choose_attack"
                
        elif self.attack_state == "wait_attack":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                if self.grenades_to_drop > 0:
                    self.last_attack = "grenades"
                    self.grenades_to_drop = 0
                else:
                    self.last_attack = "dalles"

                self.attack_cooldown = random.uniform(0.5, 2.0)
                self.attack_state = "choose_attack"

    def trigger_end_sequence(self, scene):
        # Initialise la sequence de fin selon que le boss est vaincu (explosion) ou victorieux (ecran blanc)
        if self.pv_main <= 0:
            scene.sfx_manager.play(self.death_cry)
            scene.music_manager.stop()
            

            # Chargement avec les vraies dimensions (en nombre de tuiles)
            w_tiles = 71.0 / BASE_TILE_SIZE
            h_tiles = 100.0 / BASE_TILE_SIZE
            self.explosion_frames = load_animation_sequence("assets/enemies/macron/DR_explosion",(w_tiles, h_tiles),17)
            self.is_exploding = True
            if hasattr(scene, 'sfx_manager'):
                scene.sfx_manager.play("snd_badexplosion")
            self.hide()
    
            cx, cy = self.get_center()
            self.exp_item = QGraphicsPixmapItem()
            self.exp_item.setZValue(200)
            # Positionnement centre en utilisant la taille reelle des frames
            if self.explosion_frames:
                fw = self.explosion_frames[0].width()
                fh = self.explosion_frames[0].height()
            else:
                fw = 71 * settings.scale
                fh = 100 * settings.scale
            self.exp_item.setPos(cx - fw / 2, cy - fh / 2)
            scene.addItem(self.exp_item)
            
            scene.addItem(self.exp_item)
            
        else:
            scene.sfx_manager.play("snd_macron_laugh")
            scene.music_manager.stop()
            self.white_screen = QGraphicsRectItem(0, 0, scene.width(), scene.height())
            self.white_screen.setBrush(QBrush(QColor(255, 255, 255, 0)))
            self.white_screen.setPen(QPen(Qt.NoPen))
            self.white_screen.setZValue(200)
            scene.addItem(self.white_screen)
            
            if hasattr(scene, 'player'):
                scene.player.speed = 0
                scene.player.is_effect_immune = True
                
            self.is_exploding = True
            self.explosion_timer = 0.0

    def update_explosion(self, dt, scene):
        # Gere l'animation de l'explosion du boss ou la mort du joueur apres l'ecran blanc
        if self.pv_main <= 0:
            self.explosion_timer += dt
            if self.explosion_timer >= 0.1: 
                self.explosion_timer = 0
                if self.explosion_frame_idx < len(self.explosion_frames):
                    self.exp_item.setPixmap(self.explosion_frames[self.explosion_frame_idx])
                    self.explosion_frame_idx += 1
                else:
                    scene.removeItem(self.exp_item)
                    self.die() 
                    
                    # credits de fin
                    QTimer.singleShot(3000, lambda: scene.screen_manager.go_to_credits())
        else:
            self.explosion_timer += dt
            if self.explosion_timer <= 2.0:
                alpha = int((self.explosion_timer / 2.0) * 255)
                self.white_screen.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            elif self.explosion_timer <= 3.0: # 2s de fondu + #1s d'attente
                self.white_screen.setBrush(QBrush(QColor(255, 255, 255, 255)))
            else:
                if hasattr(scene, 'player'):
                    scene.player.die()
                    
    def update_graphics(self):
        # Methode pour mettre a jour l'affichage graphique (laisser vide si gere ailleurs)
        pass
    
    def get_knockback(self, scene, source=None):
        """ Il ne donne pas de recul au joueur lorsqu'il se fait frapper"""
        pass