# -*- coding: utf-8 -*-
import math
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from game.enemies.enemy import Enemy
from game.config import BASE_TILE_SIZE, HUD_HEIGHT, DEBUG
from game.settings import settings
from game.pathfinder import get_walkable_grid, line_of_sight, is_area_walkable, astar, _pixel_to_tile, are_connected
from game.attacks.fireball import Fireball

class Wizmount(Enemy):
    def __init__(self, scale, x, y):
        super().__init__(scale, x, y)

        # --- STATS ---
        self.speed = settings.base_speed * 0.6
        self._pv_max = 6
        self.pv_main = self._pv_max
        self.aggro_range = settings.tile_size * 12
        self.damage = 0.5
        
        # --- COOLDOWN & GESTION DES PROJECTILES ---
        self.attack_cooldown = 1.0 
        self.attack_timer = 0.0
        self.projectiles = []  # Permet de traquer et mettre à jour ses propres boules de feu

        # --- LOOT ---
        self.loot = [
            ("mana", 0.75),
            ("bombe", 0.2)
        ]

        # --- HITBOX ---
        self.hitbox_offset_x = 2 / BASE_TILE_SIZE
        self.hitbox_offset_y = 1 / BASE_TILE_SIZE
        self.hitbox_width = settings.tile_size * 2 * 0.875
        self.hitbox_height = settings.tile_size * 2 * 0.875
        
        self.knockback = 1
        self.duree_knockback = 0.2

        # --- CHARGEMENT DES SPRITES (Automatisé par le moteur de base) ---
        sprite_w = settings.tile_size * 2
        sprite_h = settings.tile_size * 2

        self.sprites = {
            "up": QPixmap("assets/enemies/wizmount/wizmount_back.png").scaled(
                sprite_w, sprite_h, transformMode=Qt.FastTransformation
            ),
            "down": QPixmap("assets/enemies/wizmount/wizmount_face.png").scaled(
                sprite_w, sprite_h, transformMode=Qt.FastTransformation
            ),
            "left": QPixmap("assets/enemies/wizmount/wizmount_left.png").scaled(
                sprite_w, sprite_h, transformMode=Qt.FastTransformation
            ),
            "right": QPixmap("assets/enemies/wizmount/wizmount_right.png").scaled(
                sprite_w, sprite_h, transformMode=Qt.FastTransformation
            )
        }

        # Posture de départ
        self.direction = "down"
        self.setPixmap(self.sprites[self.direction])
        
        # offset 
        self.lock_offset_x = 0
        self.lock_offset_y = 0
        

    
    def update(self, dt, scene):
        # mise a jour des timers internes et des projectiles existants
        self._update_projectiles_and_timers(dt, scene)

        # gestion des etats prioritaires
        if self._handle_priority_states(dt, scene):
            return

        # S'il n'y a pas de cible, on s'arrête là
        if not self.target:
            return

        # 3. Verification de la portée d'agressivite
        if self._check_aggro_range(dt, scene):
            return

        # 4. Execution de la boucle principale de l'IA (Tir ou Déplacement)
        self._execute_ai_behavior(dt, scene)
        
        # . Attaque directement le joueur si superposition des hitboxes
        self.try_hit_player(scene)

    def _update_projectiles_and_timers(self, dt, scene):
        """ Gère le timer d'attaque et met à jour les boules de feu en mouvement """
        if self.attack_timer > 0:
            self.attack_timer -= dt

        for p in self.projectiles[:]:
            if p.scene() is None:
                self.projectiles.remove(p)
            else:
                p.update(dt, scene)

    def _handle_priority_states(self, dt, scene):
        """ Gère les interruptions absolues (Stun / Knockback). Retourne True si actif. """
        if self.kb_active:
            self.apply_knockback(dt, scene)
            super().update_graphics()
            self.update_damage_state(dt)
            if DEBUG:
                self.draw_debug_path(scene)
            return True
        
        if self.is_stunned:
            self.apply_stun_wiggle(dt, scene)
            super().update_graphics()
            self.update_damage_state(dt)
            self.update_stun_animation(dt)
            if DEBUG:
                self.draw_debug_path(scene)
            return True
        return False

    def _check_aggro_range(self, dt, scene):
        """ Vérifie la distance avec le joueur. Si trop loin, passe en mode errance. """
        wx, wy = self.get_center()
        px, py = self.target.get_center()
        dist = math.hypot(px - wx, py - wy)

        if dist > self.aggro_range:
            self.wander(dt, scene)
            super().update_graphics()
            self.update_damage_state(dt)
            return True
        return False

    def _execute_ai_behavior(self, dt, scene):
        """ Coeur de l'IA : Arbitre entre le tir statique ou la recherche de chemin """
        
        
        wx, wy = self.get_center()
        px, py = self.target.get_center()
        
        # priorite 1 : Fuite
        if self._handle_flee_state(dt, scene, wx, wy, px, py):
            return


        can_shoot, shoot_dir = self._check_continuous_shooting_alignment(scene)
        dx, dy = 0, 0
        
        wx, wy = self.get_center()
        px, py = self.target.get_center()
        
        # Position réellement visée avec offset
        target_x = px + self.lock_offset_x * settings.tile_size
        target_y = py + self.lock_offset_y * settings.tile_size
        
        # Vérifie si on est vraiment bien repositionné
        aligned_x = abs(wx - target_x) < settings.tile_size * 0.20
        aligned_y = abs(wy - target_y) < settings.tile_size * 0.20
        
        properly_positioned = aligned_x or aligned_y

        if can_shoot and properly_positioned:
            # --- LOGIQUE DE TIR (Logique Continue) ---
            self.path = []  # On s'arrête net pour canarder
            self.direction = shoot_dir
            if self.show_path:
                self.draw_debug_path(scene)
                
            if self.attack_timer <= 0:
                self._fire_projectile(scene)
        else:
            # --- LOGIQUE DE DÉPLACEMENT (Logique Discrète) ---
            self._update_pathfinding_target(dt, scene)
            dx, dy = self._follow_computed_path(dt)

        # Application de l'orientation selon le vecteur de déplacement final
        if dx != 0 or dy != 0:
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

        # Application physique du mouvement et rafraîchissement moteur
        self.move(dx, dy, dt, scene)
        super().update_graphics()
        self.update_stun_animation(dt)
        self.update_damage_state(dt)

    def _check_continuous_shooting_alignment(self, scene):
        """ LOGIQUE CONTINUE : Vérifie si une boule de feu de 0.5 tile de large lancée 
            depuis notre centre peut intercepter une partie de la hitbox réelle du joueur. """
        wx, wy = self.get_center()
        px, py = self.target.get_center()
        
        # Récupération sécurisée des coordonnées de la hitbox du joueur
        p_hitbox = self.target.get_hitbox()
        if hasattr(p_hitbox, 'left') and callable(p_hitbox.left):
            p_left, p_right = p_hitbox.left(), p_hitbox.right()
            p_top, p_bottom = p_hitbox.top(), p_hitbox.bottom()
        else:
            p_left = getattr(p_hitbox, 'x', px)
            p_right = p_left + getattr(p_hitbox, 'width', settings.tile_size)
            p_top = getattr(p_hitbox, 'y', py)
            p_bottom = p_top + getattr(p_hitbox, 'height', settings.tile_size)
            
        # offset_x = -settings.tile_size if px < wx else 0
        # offset_y = -settings.tile_size if py < wy else 0
        
        offset_x = self.lock_offset_x * settings.tile_size
        offset_y = self.lock_offset_y * settings.tile_size
        
        p_left += offset_x
        p_right += offset_x
        p_top += offset_y
        p_bottom += offset_y
        
        # On décale aussi px et py pour garder une ligne de mire cohérente
        px_offset = px + offset_x
        py_offset = py + offset_y

        f_half_size = (settings.tile_size * 0.5) / 2.0
        grid = get_walkable_grid(scene.room_data)

        # Cas 1 : Alignement horizontal (Le projectile se déplace sur l'axe X)
        # On regarde si l'épaisseur Y du projectile intersecte la hitbox Y du joueur
        if (wy - f_half_size < p_bottom) and (wy + f_half_size > p_top):
            direction = "right" if px > wx else "left"
            if line_of_sight((wx, wy), (px_offset, py_offset), grid, settings.tile_size, 0.5, 0.5):
                return True, direction

        # Cas 2 : Alignement vertical (Le projectile se déplace sur l'axe Y)
        # On regarde si l'épaisseur X du projectile intersecte la hitbox X du joueur
        if (wx - f_half_size < p_right) and (wx + f_half_size > p_left):
            direction = "down" if py > wy else "up"
            if line_of_sight((wx, wy), (px_offset, py_offset), grid, settings.tile_size, 0.5, 0.5):
                return True, direction

        return False, self.direction

    def _update_pathfinding_target(self, dt, scene):
        """ LOGIQUE DISCRÈTE : Recherche la tuile marchable la plus proche de Wizmount 
            qui partage la ligne/colonne de la tuile du joueur et possède un couloir dégagé de 1 tuile. """
        if not self.use_pathfinding:
            return

        self.path_timer += dt
        if self.path_timer < self.path_interval:
            return
        self.path_timer = 0.0

        grid = get_walkable_grid(scene.room_data)
        height_grid = len(grid)
        width_grid = len(grid[0]) if height_grid > 0 else 0

        wx, wy = self.get_center()
        px, py = self.target.get_center()
        
        # Identification des tuiles de départ (Wizmount) et d'arrivée (Joueur)
        e_col, e_row = _pixel_to_tile(wx, wy, settings.tile_size)
        p_col, p_row = _pixel_to_tile(px, py, settings.tile_size)

        w_tiles = max(1, math.ceil(self.hitbox_width / settings.tile_size))
        h_tiles = max(1, math.ceil(self.hitbox_height / settings.tile_size))
        
        best_target_pixel = None
        min_dist = float('inf')

        # PASSE 1 : Trouver une tuile exploitable avec une ligne de vue droite complète (largeur 1.0)
        for r in range(height_grid):
            for c in range(width_grid):
                # On ne cible que les tuiles partageant strictement la ligne ou colonne du joueur
                if c == p_col or r == p_row:
                    if is_area_walkable(grid, c, r, w_tiles, h_tiles, width_grid, height_grid):
                        cand_x = c * settings.tile_size + settings.tile_size/2
                        cand_y = (r + HUD_HEIGHT) * settings.tile_size + settings.tile_size/2
                        
                        # Vérification d'un chemin droit de 1 tuile de large (1.0, 1.0)
                        if line_of_sight((cand_x, cand_y), (px, py), grid, settings.tile_size, 1.0, 1.0):
                            d = (cand_x - wx)**2 + (cand_y - wy)**2
                            if d < min_dist:
                                min_dist = d
                                best_target_pixel = (cand_x, cand_y)

        # PASSE 2 : Fallback si le joueur est totalement caché derrière des murs
        if best_target_pixel is None:
            min_dist_fallback = float('inf')
            for r in range(height_grid):
                for c in range(width_grid):
                    if c == p_col or r == p_row:
                        if is_area_walkable(grid, c, r, w_tiles, h_tiles, width_grid, height_grid):
                            cand_x = c * settings.tile_size + settings.tile_size
                            cand_y = (r + HUD_HEIGHT) * settings.tile_size + settings.tile_size
                            d = (cand_x - wx)**2 + (cand_y - wy)**2
                            if d < min_dist_fallback:
                                min_dist_fallback = d
                                best_target_pixel = (cand_x, cand_y)

        # Détermination de la destination pour l'algorithme A*
        final_destination = best_target_pixel if best_target_pixel is not None else (px, py)
        
        
        fd_x, fd_y = final_destination
        # =========================================================
        # LOCK HORIZONTAL
        # =========================================================
        
        if px < wx - settings.tile_size * 0.25:
            self.lock_offset_x = -1
        
        elif px > wx + settings.tile_size * 0.25:
            self.lock_offset_x = 0
        
        
        # =========================================================
        # LOCK VERTICAL
        # =========================================================
        
        if py < wy - settings.tile_size * 0.25:
            self.lock_offset_y = -1
        
        elif py > wy + settings.tile_size * 0.25:
            self.lock_offset_y = 0

        # Application de l'offset basé sur la mémoire (stabilité garantie)
        fd_x += self.lock_offset_x * settings.tile_size
        fd_y += self.lock_offset_y * settings.tile_size
        # =========================================================
        # DEVERROUILLAGE SI POSITION ATTEINTE
        # =========================================================
        
        if abs(wx - fd_x) < settings.tile_size * 0.20:
            self.lock_offset_x = 0
        
        if abs(wy - fd_y) < settings.tile_size * 0.20:
            self.lock_offset_y = 0
        final_destination = (fd_x, fd_y)
        
        
        start_pos_astar = (self.x + settings.tile_size / 2.0, self.y + settings.tile_size / 2.0)
        
        # Verification rapide de connexite avant A* couteux
        if not are_connected(grid, start_pos_astar, final_destination, settings.tile_size):
            self.path = []
        else:
            new_path = astar(grid, start_pos_astar, final_destination, settings.tile_size, w_tiles, h_tiles)
            
            if new_path is not None:
                # Si on est en fallback (joueur caché), on s'arrête à une distance respectueuse (~3 cases)
                if best_target_pixel is None and len(new_path) > 3:
                    self.path = new_path[:-3]
                else:
                    self.path = new_path
            else:
                self.path = []
            
        if self.show_path:
            self.draw_debug_path(scene)
    
    def _handle_flee_state(self, dt, scene, wx, wy, px, py):
        """
        Fuite prioritaire si le joueur est trop proche
        Retourne True si l'état fuite est actif, sinon False.
        """
        flee_distance = 3 * settings.tile_size
        dist = math.hypot(px - wx, py - wy)
    
        if dist >= flee_distance:
            return False
    
        # Annule le pathfinding / tir
        self.path = []
    
        # Direction opposée au joueur
        fx = wx - px
        fy = wy - py
        norm = math.hypot(fx, fy)
    
        if norm > 0:
            fx /= norm
            fy /= norm
    
        # Double vitesse temporaire
        base_speed = self.speed
        self.speed = base_speed * 2
    
        # Mouvement direct (ignore A*)
        self.move(fx, fy, dt, scene)
    
        # Restore vitesse
        self.speed = base_speed
    
        super().update_graphics()
        self.update_stun_animation(dt)
        self.update_damage_state(dt)
    
        return True
    

    def _follow_computed_path(self, dt):
        """ Fait avancer le monstre le long du chemin A* calculé. Retourne le vecteur (dx, dy). """
        dx, dy = 0, 0
        if not self.path:
            return dx, dy

        wx, wy = self.get_center()
        next_pos = self.path[0]
        target_x, target_y = next_pos[0], next_pos[1]
        
        dx = target_x - wx
        dy = target_y - wy
        dist_to_next = math.hypot(dx, dy)
        
        # Si on est assez près du noeud actuel, on passe au suivant immédiatement
        if dist_to_next < self.speed * dt:
            self.path.pop(0)
            if self.path:
                next_pos = self.path[0]
                target_x, target_y = next_pos[0], next_pos[1]
                dx = target_x - wx
                dy = target_y - wy
                dist_to_next = math.hypot(dx, dy)

        if dist_to_next > 0:
            dx /= dist_to_next
            dy /= dist_to_next

        return dx, dy

    def _fire_projectile(self, scene):
        """ Instancie et centre parfaitement le projectile au milieu du monstre 2x2 """
        new_fireball = Fireball(self, self.direction)
        
        # Calcul des dimensions réelles de la boule de feu
        fireball_w = new_fireball.size[0] * settings.tile_size
        fireball_h = new_fireball.size[1] * settings.tile_size
        
        # Recentrage parfait basé sur la taille de Wizmount (2x2 tiles)
        new_fireball.x += (settings.tile_size * 2 - fireball_w) / 2
        new_fireball.y += (settings.tile_size * 2 - fireball_h) / 2
        new_fireball.setPos(new_fireball.x + new_fireball.anim_offset[0], new_fireball.y + new_fireball.anim_offset[1])
        
        scene.addItem(new_fireball)
        scene.projectiles.append(new_fireball)
        
        if hasattr(scene, "sfx_manager") and scene.sfx_manager:
            scene.sfx_manager.play("snd_fireball")
        
        # Reset du cooldown
        self.attack_timer = self.attack_cooldown
