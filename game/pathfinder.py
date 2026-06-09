# -*- coding: utf-8 -*-
# Auteur : essentiellement Ryan

'''
Implementation d'une intelligence artificielle aux ennemis, basee sur l'algorithme A*
'''

import heapq
import math
from game.tileset import TILE_TYPES
from game.config import HUD_HEIGHT

def get_walkable_grid(room_data,can_go_on_black=False, can_go_on_water=False):
    """
    Construit une grille 2D de booleens a partir des donnees de la salle.
    True = case accessible, False = case bloquante.
    """
    grid = []
    for row in room_data.get("tiles", []):
        grid_row = []
        for tile_id in row:
            tile_info = TILE_TYPES.get(tile_id, {})
            is_blocking = tile_info.get("collision", 0) == 1
            
            # si case bloque monstre, on regarde pour projectile
            if is_blocking:
                tile_type = str(tile_info.get("type", "")).lower()
                if can_go_on_water and ("water" in tile_type or tile_id == 4):
                    is_blocking = False
                elif can_go_on_black and ("black" in tile_type or tile_id in [3, 3.5]):
                    is_blocking = False
            
            grid_row.append(not is_blocking)
        grid.append(grid_row)
    return grid

def flood_fill(grid, col, row, visited=None):
    """
    Parcours recursif en profondeur (DFS) pour trouver l'ensemble des cases
    accessibles depuis la position (col, row) sur la grille.

    Parametres :
        grid    : grille 2D de booleens (True = accessible)
        col     : colonne de depart
        row     : ligne de depart
        visited : ensemble de cases deja visitees (usage interne)

    Retourne un ensemble de tuples (col, row) representant toutes les cases
    atteignables depuis le point de depart.
    """
    if visited is None:
        visited = set()

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # conditions d'arret : hors limites, deja visite, ou case bloquante
    if not (0 <= row < height and 0 <= col < width):
        return visited
    if (col, row) in visited:
        return visited
    if not grid[row][col]:
        return visited

    visited.add((col, row))

    # appels recursifs dans les 4 directions cardinales
    flood_fill(grid, col + 1, row, visited)
    flood_fill(grid, col - 1, row, visited)
    flood_fill(grid, col, row + 1, visited)
    flood_fill(grid, col, row - 1, visited)

    return visited


def are_connected(grid, pos_a, pos_b, tile_size):
    """
    Verifie si deux positions pixel sont dans la meme zone accessible
    de la grille, en utilisant le flood fill recursif.

    Permet d'eviter un appel A* couteux lorsque la cible est inatteignable.

    Parametres :
        grid      : grille 2D de booleens
        pos_a     : coordonnees pixel (x, y) du premier point
        pos_b     : coordonnees pixel (x, y) du second point
        tile_size : taille d'une case en pixels

    Retourne True si les deux points sont connectes, False sinon.
    """
    col_a, row_a = _pixel_to_tile(pos_a[0], pos_a[1], tile_size)
    col_b, row_b = _pixel_to_tile(pos_b[0], pos_b[1], tile_size)

    reachable = flood_fill(grid, col_a, row_a)
    return (col_b, row_b) in reachable 
def heuristic(a, b):
    """Distance euclidienne entre deux cases de la grille."""
    return math.hypot(a[0] - b[0], a[1] - b[1])

def _pixel_to_tile(x, y, tile_size):
    """Convertit des coordonnees pixel en indices de case (col, row)."""
    col = int(x // tile_size)
    row = int((y - HUD_HEIGHT * tile_size) // tile_size)
    return (col, row)

def _tile_center(col, row, tile_size):
    """Retourne les coordonnees pixel du centre d'une case."""
    tx = col * tile_size + tile_size / 2.0
    ty = (row + HUD_HEIGHT) * tile_size + tile_size / 2.0
    return (tx, ty)

def is_area_walkable(grid, col, row, w_size, h_size, width, height):
    """
    verifie est block de size x est libre a partir de (col,row)
    """
    for r in range(row, row + h_size):
        for c in range(col, col + w_size):
            if not (0 <= r < height and 0 <= c < width) or not grid[r][c]:
                return False
    return True

def line_of_sight(start_pos, end_pos, grid, tile_size, w_size, h_size):
    """
    Verifie s'il existe une ligne de vue degagee entre deux points en coordonnees pixel.
    Utilise un raycasting par pas de tile_size/4, en testant les 4 coins
    de la hitbox de l'entite pour eviter les clips dans les angles.

    Retourne True si le chemin est libre, False s'il est bloque ou hors grille.
    
    prend en compte la taille de l'entite
    """
    x0, y0 = start_pos
    x1, y1 = end_pos

    dx = x1 - x0
    dy = y1 - y0
    distance = math.hypot(dx, dy)
    
    if distance == 0:
        return True
        
    dx /= distance
    dy /= distance
    
    step_size = tile_size / 4.0
    steps = int(distance / step_size)
    
    height_grid = len(grid)
    width_grid = len(grid[0]) if height_grid > 0 else 0
    
    # # On définit les coins du rectangle
    # margin_w = (tile_size * w_size) * 0.95
    # margin_h = (tile_size * h_size) * 0.95
    # offsets = [(0, 0), 
    #            (margin_w, 0), 
    #            (0, margin_h), 
    #            (margin_w, margin_h)
    # ]
    
    
    half_w = (tile_size * w_size) * 0.9 / 2.0
    half_h = (tile_size * h_size) * 0.9 / 2.0
    
    offsets = [
        (-half_w, -half_h),  # Haut-Gauche
        (half_w, -half_h),   # Haut-Droite
        (-half_w, half_h),   # Bas-Gauche
        (half_w, half_h)     # Bas-Droite
    ]
    
    for i in range(steps + 1):
        bx = x0 + dx * (i * step_size)
        by = y0 + dy * (i * step_size)
        
        for ox, oy in offsets:
            cx = bx + ox
            cy = by + oy
            
            col, row = _pixel_to_tile(cx, cy, tile_size)
            
            if not (0 <= row < height_grid and 0 <= col < width_grid and grid[row][col]):
                    return False
                
    return True

def smooth_path(path_pixels, grid, tile_size, w_size, h_size):
    """
    Lisse un chemin par elagage de ficelle (String Pulling) :
    si le point C est visible depuis le point A, le point intermediaire B est supprime.

    Prend une liste de coordonnees pixel et retourne une version allégée.
    """
    if len(path_pixels) <= 2:
        return path_pixels
        
    smoothed = [path_pixels[0]]
    current_index = 0
    
    while current_index < len(path_pixels) - 1:
        furthest = current_index + 1
        for i in range(current_index + 2, len(path_pixels)):
            if line_of_sight(path_pixels[current_index], path_pixels[i], grid, tile_size, w_size, h_size):
                furthest = i
            else:
                break
                
        smoothed.append(path_pixels[furthest])
        current_index = furthest
        
    return smoothed

def astar(grid, start_pos, goal_pos, tile_size, w_size, h_size):
    """
    Calcule un chemin optimal entre deux points via l'algorithme A*.

    Parametres :
        grid      : grille 2D de booleens (True = accessible)
        start_pos : coordonnees pixel de depart (x, y)
        goal_pos  : coordonnees pixel d'arrivee (x, y)
        tile_size : taille d'une case en pixels

    Retourne une liste de coordonnees pixel (x, y) représentant le chemin
    lissé, ou None si aucun chemin n'est trouvé.

    Details :
        - Deplacement en 8 directions avec cout 1 (cardinal) ou 1.414 (diagonal)
        - Coupure de coin interdite sur la grille discrete
        - Le chemin final est lissé par String Pulling (voir smooth_path)
    """
    if not grid or not grid[0]:
        return None

    height = len(grid)
    width = len(grid[0])

    # start_tile = _pixel_to_tile(start_pos[0], start_pos[1], tile_size)
    # goal_tile = _pixel_to_tile(goal_pos[0], goal_pos[1], tile_size)
    
    # Retrouve la tuile de coin "Top-Left" pour l'analyse de zone de la grille discrète
    start_tl_x = start_pos[0] - (w_size * tile_size) / 2.0 + tile_size / 2.0
    start_tl_y = start_pos[1] - (h_size * tile_size) / 2.0 + tile_size / 2.0
    start_tile = _pixel_to_tile(start_tl_x, start_tl_y, tile_size)

    goal_tl_x = goal_pos[0] - (w_size * tile_size) / 2.0 + tile_size / 2.0
    goal_tl_y = goal_pos[1] - (h_size * tile_size) / 2.0 + tile_size / 2.0
    goal_tile = _pixel_to_tile(goal_tl_x, goal_tl_y, tile_size)

    if not is_area_walkable(grid, goal_tile[0], goal_tile[1], w_size, h_size, width, height):
        return None

    sx = max(0, min(start_tile[0], width - 1))
    sy = max(0, min(start_tile[1], height - 1))
    start_clamped = (sx, sy)

    frontier = []
    heapq.heappush(frontier, (0, start_clamped))
    
    came_from = {start_clamped: None}
    cost_so_far = {start_clamped: 0}
    
    while frontier:
        _, current = heapq.heappop(frontier)
        
        if current == goal_tile:
            break
            
        x, y = current
        neighbors = [
            (x+1, y), (x-1, y), (x, y+1), (x, y-1),
            (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)
        ]
        
        for nx, ny in neighbors:
            if 0 <= ny < height and 0 <= nx < width:
                if is_area_walkable(grid, nx, ny, w_size, h_size, width, height):
                    # Interdit de couper un coin diagonal si l'une des cases adjacentes est bloquante
                    if nx != x and ny != y:
                        if not is_area_walkable(grid, x, ny, w_size, h_size, width, height) or \
                            not is_area_walkable(grid, nx, y, w_size, h_size, width, height):
                            continue
                    
                    step_cost = 1 if nx == x or ny == y else 1.414
                    new_cost = cost_so_far[current] + step_cost
                    
                    if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                        cost_so_far[(nx, ny)] = new_cost
                        priority = new_cost + heuristic((nx, ny), goal_tile)
                        heapq.heappush(frontier, (priority, (nx, ny)))
                        came_from[(nx, ny)] = current
                        
    if goal_tile not in came_from:
        return None
        
    path_tiles = []
    current = goal_tile
    while current != start_clamped:
        path_tiles.append(current)
        current = came_from[current]
        
    path_tiles.reverse()
    
    path_pixels = [start_pos]
    offset_x = (w_size * tile_size) / 2.0
    offset_y = (h_size * tile_size) / 2.0
    for i, tile in enumerate(path_tiles):
        if i == len(path_tiles) - 1:
            path_pixels.append((goal_pos[0], goal_pos[1]))
        else:
            tx = tile[0] * tile_size + offset_x
            ty = (tile[1] + HUD_HEIGHT) * tile_size + offset_y
            path_pixels.append((tx, ty))
            #path_pixels.append(_tile_center(tile[0], tile[1], tile_size))
            
    smoothed = smooth_path(path_pixels, grid, tile_size, w_size, h_size)
    
    if smoothed and smoothed[0] == start_pos:
        smoothed.pop(0)
        
    return smoothed
