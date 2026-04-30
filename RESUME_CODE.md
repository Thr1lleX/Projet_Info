# 📦 Résumé du dossier `game/`

> Style TDAH : bullet points, court, direct. Pas de blabla inutile.

---

## ⚙️ `config.py` — Les constantes globales
Pas de fonctions. Juste des variables partagées partout :
- `TILE_SIZE` = taille d'une case en pixels (16 × scale)
- `GRID_WIDTH / GRID_HEIGHT` = taille de la grille de jeu (16×11)
- `BASE_SPEED` = vitesse de base des entités
- `FPS` / `interval` = fréquence de la boucle de jeu
- `KEYS` = mapping clavier (flèches, W, X, Echap, etc.)
- `DEBUG` = active/désactive les hitboxes et logs
- `DURATION_FADE_*` = durées des transitions de salle

---

## 🖼️ `animspr.py` — Animations de sprites

### `load_animation_sequence(folder_path, frame_count, size)`
- Charge une liste d'images numérotées (`sprite1.png`, `sprite2.png`...)
- Les redimensionne à la bonne taille en tiles
- Retourne une liste de frames (QPixmap)

### `generate_directional_animations(base_frames, pos, size)`
- Prend des frames (supposées vers le haut) et les tourne dans les 4 directions
- Calcule l'offset de position pour que le sprite reste centré sur le joueur après rotation
- Retourne un dict `{"up": {"frames": [...], "offset": (x,y)}, "left": ..., ...}`

---

## ⚔️ `attack.py` — Classe de base Attack
- Juste une classe vide `Attack(QGraphicsPixmapItem)` 
- **En construction**, pas encore utilisée directement

---

## 🖋️ `fonts.py` — Chargement de polices

### `get_font(path, size, bold)`
- Charge une police depuis un fichier `.ttf` une seule fois (mise en cache)
- Si la police est introuvable → fallback sur Arial
- Retourne un `QFont` prêt à l'emploi

### `get_font0(size)` / `get_font1(size)`
- Raccourcis pour charger les polices du projet (`8bitoperator.ttf`, `undertale-wingdings.ttf`)

---

## 🎵 `music.py` — Gestionnaire de musique (`MusicManager`)

### `__init__`
- Crée le player audio en boucle infinie, initialise l'état à `"idle"`

### `on_status_changed()`
- Callback automatique : lance la lecture quand le son est prêt, affiche erreur sinon

### `play(music_name, fade_in=0)`
- Joue une musique `.wav` (avec fade in optionnel)
- Si c'est déjà la même musique → rien ne se passe
- Sinon → stop l'actuelle, charge la nouvelle de façon asynchrone

### `play_mp3(music_name, fade_in=0)`
- Même chose mais pour les fichiers `.mp3` (pour les gros fichiers > 25 Mo)

### `_load_pending()`
- Appelée en différé pour charger le fichier audio sans freezer le jeu

### `update(dt)`
- À appeler chaque frame : gère les effets de **fade in** et **fade out** du volume

### `stop()`
- Stop la musique, reset l'état

### `start_fade_out()`
- Lance un fade out progressif du volume

---

## 🎶 `sfx.py` — Gestionnaire d'effets sonores (`SFXManager`)
> Utilise pygame (séparé de PyQt pour les performances)

### `__init__`
- Init le mixer pygame (48kHz, 32 canaux simultanés)
- Précharge tous les sons au démarrage

### `_preload_all_sounds()`
- Parcourt le dossier `sound_effect/` et charge tous les `.wav` en RAM
- Évite les freezes quand un son se joue pour la première fois

### `play(name)`
- Joue un son par son nom (ex: `"snd_playerhit1"`)
- Ne bloque jamais le CPU

### `set_volume(volume)`
- Règle le volume global des effets sonores (0.0 à 1.0)

---

## 🪟 `window.py` — La fenêtre de jeu (`GameWindow`)

### `__init__`
- Crée la fenêtre à taille fixe, y attache la `GameScene`
- Désactive les scrollbars

### `keyPressEvent(event)` / `keyReleaseEvent(event)`
- Transmet les touches au joueur ET à la scène

### `closeEvent(event)`
- Stop la musique proprement à la fermeture

### `quitter_jeu()`
- Stop la musique, ferme la fenêtre, quitte PyQt

---

## 🗺️ `scene.py` — La scène de jeu (`GameScene`)

### `__init__`
- Initialise tout : tileset, joueur, ennemis, transition, musique, sfx
- Lance la game loop via un `QTimer`

### `draw_hud()`
- Dessine un rectangle noir en haut de l'écran (la barre HUD)

### `game_loop()`
- Appelée 60× par seconde
- Met à jour : joueur, ennemis, transitions, musique
- Stop tout si game over

### `is_blocking_rect(x, y, w, h)`
- Vérifie si un rectangle (hitbox) entre en collision avec un tile solide ou un bord de salle
- Retourne `True` si bloqué, `False` sinon

### `draw_room(room)`
- Dessine toutes les tiles de la salle depuis le JSON
- Affiche les collisions en bleu en mode DEBUG
- Spawn les ennemis

### `_change_room_internal(room_name, direction)`
- Change de salle : charge le JSON, nettoie la scène (sauf items persistants), redessine

### `check_room_transition()`
- Vérifie si le joueur sort par un bord → lance la transition vers la salle suivante

### `start_room_music()`
- Lance la musique associée à la salle actuelle (avec fade in si spécifié dans le JSON)

### `room_music_changed()`
- Retourne `True` si la musique de la nouvelle salle est différente de l'actuelle

### `next_room_music_changed(room_name)`
- Même chose mais pour la salle suivante (avant même d'y entrer)

### `reposition_player(direction)`
- Replace le joueur de l'autre côté de l'écran après un changement de salle

### `spawn_enemies(room)`
- Lit les ennemis du JSON de la salle et les instancie
- Skip les ennemis déjà tués dans la session

### `game_over()`
- Stop le gameplay, vide la scène, affiche un écran noir, joue la musique de game over

---

## 🏃 `entity.py` — Classe de base de toutes les entités (`Entity`)

### `get_hitbox(x, y)`
- Retourne `(x, y, w, h)` de la hitbox réelle (avec offset)

### `get_center()`
- Retourne le centre de la hitbox en pixels

### `move(dx, dy, dt, scene)`
- Déplace l'entité en tenant compte des collisions (axe X et Y séparément)

### `take_damage(scene, damage, source)`
- Retire des PV, applique flash rouge, knockback, invulnérabilité
- Si PV ≤ 0 → appelle `die()`

### `die()`
- Retire l'entité de la liste ennemis et la rend invisible

### `apply_red_flash()`
- Teinte tous les sprites en rouge semi-transparent (effet de dégât visuel)

### `get_knockback(scene, source)`
- Calcule direction + vitesse du knockback depuis la source
- **Ne déplace pas encore** → stocke les paramètres pour `apply_knockback`

### `apply_knockback(dt, scene)`
- Applique le déplacement de knockback pixel par pixel (avec gestion des collisions)

### `_move_with_collision_limit(axis, amount)`
- Déplace sur un axe en s'arrêtant si collision ou bord de carte

### `_is_out_of_bounds(x, y)`
- Vérifie si la hitbox sort des limites de la salle

### `update_graphics()`
- Met à jour le sprite affiché (selon direction) et la position
- Met à jour la hitbox DEBUG si activée

### `update_damage_state(dt)`
- Gère les timers de : flash rouge, invulnérabilité, immunité aux effets, stun

### `apply_stun_wiggle(dt, scene)`
- Fait osciller l'entité latéralement pendant le stun (effet visuel)

### `stun(duration, wiggle=True)`
- Applique un stun (bloque mouvements + attaques) + immunité aux effets
- Optionnel : petit wiggle visuel

### `update(dt, scene)` *(abstraite)*
- À redéfinir dans chaque sous-classe

---

## 🧑 `player.py` — Le joueur (`Player`)

### `key_press(key)` / `key_release(key)`
- Ajoute/retire les touches actives dans un set

### `update(dt, scene)`
- Priorités : knockback > stun > attaque en cours > mouvement normal
- Gère direction, mouvements, attaque épée, lance, cri (M)
- Normalise les déplacements en diagonale

### `get_hitbox(x, y)`
- Override : hitbox légèrement plus petite que le sprite

### `die()`
- Appelle `scene.game_over()`

### `handle_exit_logic(dt, scene)`
- Gère le maintien de la touche Echap pour quitter
- Affiche un texte `EXIT...` progressif

### `trigger_quit(scene)`
- Stop le timer de la scène et ferme la fenêtre proprement

### `attack(scene)`
- Crée un objet `SwordSlash` et l'ajoute à la scène
- Joue un son de voix aléatoire

### `shout(scene)`
- Joue juste un son de test (touche M)

### `spear(scene)`
- Crée un objet `Spear` et l'ajoute à la scène

---

## 🔁 `transition.py` — Transitions entre salles (`TransitionManager`)

### `__init__(scene)`
- Crée un overlay noir transparent par-dessus toute la scène

### `start(room_name, direction)`
- Lance la transition : fade out → changement de salle → fade in → attente musique

### `update(dt)`
- Machine à états : `fade_out` → `change_room` → `fade_in` → `music_wait` → `idle`
- Gère aussi le fade out de la musique si la salle suivante a une musique différente

---

## 📄 `room_loader.py` — Chargement de salle

### `load_room(path)`
- Lit un fichier JSON et retourne les données de la salle (tiles, ennemis, transitions, musique)

---

## 🧱 `tileset.py` — Types de tiles
Pas de fonctions. Juste un dict `TILE_TYPES` :
- `0` = sable (pas de collision)
- `1` = arbre (collision solide)

---

## 👾 `enemies/enemy.py` — Classe de base ennemis (`Enemy`)

### `set_target(target)`
- Définit la cible de l'ennemi (en général le joueur)

### `update(dt, scene)`
- Knockback > stun > fonce vers le joueur si dans la portée d'aggro
- Appelle `try_hit_player` à chaque frame

### `die()`
- Enregistre l'ennemi comme "tué" dans la session (pour pas le respawn)
- Appelle `super().die()`

### `try_hit_player(scene)`
- Vérifie collision AABB avec la cible
- Si collision → inflige dégâts + knockback + stun éventuel

---

## 📋 `enemies/enemy_registry.py`

### `load_enemy_types()`
- Scanne automatiquement le dossier `enemies/`
- Importe chaque fichier et enregistre la classe ennemie dans un dict `{nom: Classe}`
- Le nom du fichier doit matcher le nom de la classe

### `ENEMY_TYPES`
- Dict résultat utilisé par la scène pour instancier les ennemis depuis le JSON

---

## 🟥 `enemies/placeholder1.py` — Ennemi basique (`Placeholder1`)
- Hérite de `Enemy`, lent (vitesse/3), 2 PV
- Sprite unique dans toutes les directions
- Comportement IA hérité de `Enemy` (fonce sur le joueur)

---

## 🟦 `enemies/placeholder2.py` — Ennemi boss (`Placeholder2`)
- Hérite de `Enemy`, très lent mais costaud : 10 PV, 2 dégâts, stun de 5s, knockback ×5
- Hitbox 2×2 tiles
- Invulnérabilité longue (1.5s)

### `die()`
- 1 chance sur 11 : ouvre une fenêtre Rick Astley 🎵

### `rick()`
- Crée et affiche une `RickWindow`

---

## 🤡 `rick.py` — Easter egg Rick Astley (`RickWindow`)

### `__init__(music_manager)`
- Fenêtre popup avec un GIF de Rick Astley + musique `mus_rick.mp3`

### `closeEvent(event)`
- Stop la musique quand on ferme la fenêtre

---

## 🗡️ `attacks/sword_slash.py` — Attaque épée (`SwordSlash`)

### `__init__(player, direction, duration)`
- Charge les frames d'animation et les tourne dans la bonne direction
- Définit la hitbox frame par frame (données brutes en pixels 16×16)

### `update_position()`
- Repositionne le sprite d'attaque collé au joueur (avec offset de rotation)

### `update_hitbox()`
- Met à jour la hitbox selon la frame actuelle + direction (rotation des coins)

### `rotate_point(x, y, direction)`
- Tourne un point de la hitbox (up/left/right/down) avec son offset

### `check_collisions(scene)`
- Détecte les ennemis dans la zone de hitbox
- Inflige dégâts + knockback à l'ennemi
- Donne aussi un léger recul au joueur (effet de "choc")

### `update(dt, scene)`
- Avance l'animation frame par frame
- Appelle `check_collisions` à chaque frame
- Si animation terminée → `die()`

### `die()`
- Retire le sprite de la scène, repasse `player.is_attacking = False`

### `get_center()`
- Retourne le centre de la hitbox (pour les calculs de knockback)

---

## 🏹 `attacks/spear.py` — Attaque lance (`Spear`)
> Même structure que `SwordSlash`, juste des stats différentes :
- Dégâts × 3
- Pas de knockback donné au joueur
- Pas de stun
- Animation 1×4 tiles (lance longue portée)
- `die()` repasse `player.is_usingspear = False`
