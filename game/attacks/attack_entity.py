# -*- coding: utf-8 -*-

# Auteur : essentiellement Mateo

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem
#from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtGui import QPen, QColor
from game.config import TILE_SIZE, DEBUG, SCALE, BASE_TILE_SIZE
from abc import abstractmethod

from game.animspr import load_animation_sequence, generate_directional_animations
from game.sfx import SFXManager


class AttackEntity(QGraphicsPixmapItem):
    """
    Le but de cette classe est de generaliser la notion d'attaques et projectiles 
    a l'ecran
    Nos attaques au corps a corps (MeleeAttack et projectiles heritent donc de cette classe.
    """
    def __init__(self, source, direction, damage, duration = None):
        """
        source pour eviter de se toucher soi meme et calculer effets (knockback, stats...)
        direction pour anime et hitbox
        damage ok
        duration = None (infini, projectile)
        
        """
        super().__init__()
        self.source = source
        self.direction = direction
        
        # --- PARAMETRES D'ATTAQUE ---
        self.damage = damage
        self.knockback = self.source.knockback
        self.duree_knockback = self.source.duree_knockback # knockback inflige a la cible en terme de tiles
        self.give_player_knockback = False
        self.do_stun = 0  # 0 = aucun stun, x = duree
        self.can_go_on_water = False
        self.can_hit_source = False
        
        # VISUELS
        self.setZValue(99) #voir doc setZvalue.txt
        
        self.duration = duration
        self.elapsed_time = 0 # duree totale depuis lancement de l'objet
        
        self.targets_hit = set()
        
        
        # --- PARAMETRES DE HITBOX ET ANIMATION ---
        self.raw_hitbox_data = {
        }
        
        self.frames = []        
        self.current_frame = 0
        
        self.anim_timer = 0
        self.anim_speed = 0
        
        self.loop = False

        self.debug_rect = QGraphicsRectItem(self)
        self.debug_rect.setPen(QPen(QColor("blue"), 1))

        if not DEBUG:
            self.debug_rect.hide()


    @abstractmethod
    def update_position(self):
        pass

    def update(self, dt, scene):
        self.elapsed_time += dt
    
        self.update_position()
    
        self.update_hitbox()
        self.check_collisions(scene)
    
        if self.duration is not None and self.elapsed_time >= self.duration:
            self.die()

    def update_hitbox(self):
        """
        setRect fais un rectangle pour du (x,y,w,h)
        """
        # +1 pour correspondance entre navigage de frame (0...n-1) et nom frame (1...n)
        data = self.raw_hitbox_data.get(self.current_frame+1) 
    
        if not data:
            self.debug_rect.hide()
            return
        
        (x1, y1), (x2, y2) = data
        
        x1, y1 = self.transform_point(x1,y1)
        x2, y2 = self.transform_point(x2,y2)
        
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x1 - x2), abs(y1 - y2)
        
        # c'est ma hitbox, show ssi DEBUG
        self.debug_rect.setRect(
            x * SCALE,
            y * SCALE,
            w * SCALE,
            h * SCALE
        )
        
        if DEBUG:
            self.debug_rect.show()

    def transform_point(self, x, y):
        return x,y

    @abstractmethod
    def die(self):
        # if self.scene():
        #     self.scene().removeItem(self)

        # self.source.is_attacking = False
        """
        faut refaire à chaque fois cette fonction pour pas confondre
        les self.source.is_attacking, is_using.item etc.
        """
        pass

    def get_center(self):
        rect = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()
        return (rect.center().x(), rect.center().y())
        
        

    def check_collisions(self, scene):
        """
        Fonction qui va generer knockback au joueur 
        par rapport a position de l'epee et de l'ennemi
        comme si l'ennemi nous avait frappe
        """
        hitbox_zone = self.debug_rect.mapToScene(
            self.debug_rect.rect()
        ).boundingRect()
    
        for item in scene.items(hitbox_zone):
            if (
                hasattr(item, "take_damage")
                and (item != self.source or self.can_hit_source)
                and item not in self.targets_hit
            ):
                # degats + knockback ennemi (source = epee)
                item.take_damage(scene, self.damage, self)
                item.stun(self.do_stun)
                self.targets_hit.add(item)
    
                # knockback du joueur (recul)
                # direction = epee -> joueur
                # intensite + duree = ennemi
                if self.give_player_knockback:
    
                    old_kb = self.knockback
                    old_duration = self.duree_knockback
        
                    self.knockback = item.knockback
                    self.duree_knockback = item.duree_knockback
        
                    self.source.get_knockback(scene, self)
        
                    # restore
                    self.knockback = old_kb
                    self.duree_knockback = old_duration
            
            

# Differenciation des classes selon si l'attaque dure ou non

class TemporaryAttack(AttackEntity):
    """
    Classe pour les attaques qui durent le temps de leur animation
    Typiquement, armes de melee & bombes
    Attention, on ne fait pas la rotation des bombes, voir MeleeAttack
    """

    def __init__(self, source, direction, damage, duration):
        super().__init__(source, direction, damage, duration)
        self.loop = False
        
        self.setZValue(97)
        
        
    def update(self, dt, scene):
        """
        update specifique aux attaques peristantes
        """
        self.update_position()

        self.anim_timer += dt

        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.current_frame += 1

            if self.current_frame < len(self.frames):
                self.setPixmap(self.frames[self.current_frame])
                self.update_hitbox()
                self.check_collisions(scene)
            else:
                self.die()

    def update_position(self):
        """
        Applique l'offset statique pour centrer l'explosion.
        """
        self.setPos(self.x + self.anim_offset[0], self.y + self.anim_offset[1])
                

class MeleeAttack(TemporaryAttack):
    """
    Classe pour les attaque de melee, qui restent pres du joueur 
    et tournent autour de lui selon direction (epee, spear...)
    """
    def __init__(self, source, direction, damage, duration, spr_path, nb_frames, size, pos):
        super().__init__(source, direction, damage, duration)
        self.setZValue(98)
        self.spr = spr_path
        self.nb_frames = nb_frames
        self.size = size
        self.pos = pos
        
        # recupere frames ainsi qu'offset
        self.animation_sequence = load_animation_sequence("assets/"+self.spr,self.size,self.nb_frames)
        self.gen_anim_direct = generate_directional_animations(self.animation_sequence, self.pos,self.size)[self.direction]
        self.frames = self.gen_anim_direct["frames"]
        self.anim_offset = self.gen_anim_direct["offset"] #en pxl!
        
        self.anim_speed = self.duration / len(self.frames)
        
        self.setPixmap(self.frames[self.current_frame])

        self.give_player_knockback = True
    
    def update_position(self):
        """
        donne la position comme les autres update
        
        CEPENDANT, on va offset la position par rapport à la rotation
        Voir feuilles avec logique, 
        ou sinon juste regarder la formule de generate_directional_animations
        
        qt nous place dans le coin haut-gauche (0,0), coincide avec position du joueur
        donc on doit offset d'un certain nb de tile (convertis en pixels precedemment)
        """

        x = self.source.x + self.anim_offset[0]
        y = self.source.y + self.anim_offset[1]

        self.setPos(x, y)


            
    def transform_point(self, x,y):
        """
        On override la transformation linéaire pour appliquer notre rotation.
        Ainsi,update_hitbox donne la hitbox et la retourne et recentre 
        selon la direction (self.direction) 
        """
        (nx, ny), offset = self.rotate_point(x, y, self.direction)
        return nx + offset[0], ny + offset[1]

    def rotate_point(self,x,y,direction):
        """
        Fonction pour rotation autour de 0,0 un point de la hitbox 
        renvoie aussi offset

        Parameters
        ----------
        x : int
            abscisse en pxl.
        y : int
            ordonnee en pxl.
        direction : str
            "up","left","right","down".
        -------
        nouevelles coordonnees + offset.

        """
        # pour la logique fait un dessin, simple a comprendre
        if direction == "up":
            offset = (0,0)
            new_coord = x,y
            return (new_coord,offset)
        elif direction == "left":
            offset = (0,self.size[0]*BASE_TILE_SIZE)
            new_coord = y,-x
            return (new_coord,offset)

        elif direction == "right":
            offset = (self.size[1]*BASE_TILE_SIZE,0)
            new_coord = -y,x
            return (new_coord,offset)
        else:
            offset = (self.size[0]*BASE_TILE_SIZE,self.size[1]*BASE_TILE_SIZE)
            new_coord = -x,-y
            return (new_coord,offset)
        # je sais pas pk on *BASE_TILE_SIZE et pas TILE_SIZE, mais seul qui fonctionnait


class PersistentAttack(AttackEntity):
    """
    Classe pour les attaques qui durent dans le temps de façon infinie
    Se déplace indépendamment de la source et meurt à la collision.
    Typiquement un projectile
    Joue son animation en boucle
    """
    def __init__(self, source, direction, damage, spr_path, nb_frames, size, pos, speed):
        super().__init__(source, direction, damage, duration=None)
        self.loop = True
        self.setZValue(99)
        
        self.only_one = False #par defaut on peut lancer plusieurs projectiles
        
        self.spr = spr_path
        self.nb_frames = nb_frames
        self.size = size
        self.pos = pos
        self.projectile_speed = speed # en tiles/seconde
        
        # on initilise la position de depart sur le joueur, d'ou la logique de rot de melee
        self.x = self.source.x
        self.y = self.source.y
        self.setPos(self.x, self.y)
        
        self.animation_sequence = load_animation_sequence("assets/"+self.spr, self.size, self.nb_frames)
        self.gen_anim_direct = generate_directional_animations(self.animation_sequence, self.pos, self.size)[self.direction]
        self.frames = self.gen_anim_direct["frames"]
        self.anim_offset = self.gen_anim_direct["offset"]
        
        self.anim_speed = 0.1 # en frame par seconde
        self.setPixmap(self.frames[self.current_frame])
        
        self.current_dt = 0

    def update(self, dt, scene):
        """
        boucle d'animation
        """
        self.current_dt = dt
        self.elapsed_time += dt

        self.update_position()
        
        # boucle infinie
        if self.anim_speed > 0:
            time_per_frame = 1.0 / self.anim_speed
            
            self.anim_timer += dt
            
            if self.anim_timer >= time_per_frame:
                self.anim_timer -= time_per_frame
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.setPixmap(self.frames[self.current_frame])

        self.update_hitbox()
        self.check_collisions(scene)

    def update_position(self):
        """
        mouvement de base en ligne droite, 
        a override si on veut une autre loi de deplacement
        """
        move_dist = self.projectile_speed * TILE_SIZE * self.current_dt

        if self.direction == "up":
            self.y -= move_dist
        elif self.direction == "down":
            self.y += move_dist
        elif self.direction == "left":
            self.x -= move_dist
        elif self.direction == "right":
            self.x += move_dist
            
        self.setPos(self.x + self.anim_offset[0], self.y + self.anim_offset[1])

    def check_collisions(self, scene):
        """
        simple a comprendre, collision avec entites + murs
        """
        hitbox_zone = self.debug_rect.mapToScene(self.debug_rect.rect()).boundingRect()
        hx, hy = hitbox_zone.x(), hitbox_zone.y()
        hw, hh = hitbox_zone.width(), hitbox_zone.height()
        
        # collision avec bords de l'ecran
        marge = 0 * TILE_SIZE
        limit_left = 0 - marge
        limit_right = (16 * TILE_SIZE) + marge
        limit_top = (2 * TILE_SIZE) - marge
        limit_bottom = (13 * TILE_SIZE) + marge
        if (hx < limit_left) or (hx + hw > limit_right) or (hy < limit_top) or (hy + hh > limit_bottom):
            scene.sfx_manager.play("snd_woodhit")
            self.die()
            return

        # collisions avec murs
        if scene.is_blocking_rect(
                hitbox_zone.x(),
                hitbox_zone.y(),
                hitbox_zone.width(),
                hitbox_zone.height(),
                entity = self
        ):
            scene.sfx_manager.play("snd_woodhit")
            self.die()
            return
        # collision avec ennemis
        for item in scene.items(hitbox_zone):
            if item != self.source and item != self:
                # si touche ennemi, disparait
                if hasattr(item, "take_damage") and item not in self.targets_hit:
                    item.take_damage(scene, self.damage, self)
                    item.stun(self.do_stun)
                    self.targets_hit.add(item)
                    scene.sfx_manager.play("snd_woodhit")
                    self.die() 
                    return
                
    # def die(self):
    #     """ 
    #     suppression du projectile du jeu 
    #     """
    #     if self.scene():
    #         self.scene().removeItem(self)
    def die(self):
        """
        joue une animation de fin puis supprime le projectile
        """
        # si eviter double appel
        if hasattr(self, "dying") and self.dying:
            return
    
        self.dying = True
    
        poof_sequence = load_animation_sequence(
            "assets/player/attack/poof",
            (1, 1),
            3
        )
    
        self.frames = poof_sequence
        self.current_frame = 0
        self.setPixmap(self.frames[0])
    
        self.projectile_speed = 0
        self.anim_timer = 0
        self.anim_speed = 15

        self.update = self.update_death

    def update_death(self, dt, scene):
        self.anim_timer += dt
        time_per_frame = 1.0 / self.anim_speed
    
        if self.anim_timer >= time_per_frame:
            self.anim_timer -= time_per_frame
            self.current_frame += 1
    
            if self.current_frame >= len(self.frames):
                if self.scene():
                    self.scene().removeItem(self)
                return
    
            self.setPixmap(self.frames[self.current_frame])

    def transform_point(self, x, y):
        (nx, ny), offset = self.rotate_point(x, y, self.direction)
        return nx + offset[0], ny + offset[1]

    def rotate_point(self, x, y, direction):
        if direction == "up":
            return (x, y), (0, 0)
        elif direction == "left":
            offset = (0, self.size[0] * BASE_TILE_SIZE)
            return (y, -x), offset
        elif direction == "right":
            offset = (self.size[1] * BASE_TILE_SIZE, 0)
            return (-y, x), offset
        else:
            offset = (self.size[0] * BASE_TILE_SIZE, self.size[1] * BASE_TILE_SIZE)
            return (-x, -y), offset
