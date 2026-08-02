# Emby's Quest : Tuntsu

A fully functional top-down action-RPG built from scratch in Python, inspired by the retro *Legend of Zelda* era on the NES. The game runs on **PyQt5** — a general-purpose GUI framework, not a game engine — which made building the game loop, rendering, collision, and enemy AI a from-the-ground-up engineering exercise.

> Student project developed for the *Projet Informatique* course at ENSTA – Institut Polytechnique de Paris. All graphics and audio are original assets; the game is non-commercial and made for learning.

Itch.io link for direct download :

https://matonphare.itch.io/embys-quest


---

## Highlights

- **Custom engine on top of PyQt5** — game loop, rendering, and physics built from scratch on `QGraphicsScene` / `QGraphicsView`, without a dedicated game framework.
- **Enemy AI with A\* pathfinding** — grid-based A* with a Euclidean heuristic, line-of-sight shortcutting, and String-Pulling path smoothing; benchmarked at ~5% of a single frame's budget at 60 FPS.
- **Recursive flood-fill connectivity checks** — a DFS reachability test short-circuits expensive A* calls when the target is structurally unreachable.
- **Clean OOP architecture** — 40+ classes over a 4-level inheritance hierarchy, with several design patterns applied deliberately (State, Registry, Composite).
- **Data-driven levels** — every one of the 100+ rooms is described declaratively in JSON (tiles, spawns, transitions, biome, conditional flags), making levels easy to author and edit.
- **Tested** — 41 unit tests covering the logic that can be isolated from the GUI, plus a dedicated A* benchmark script.

---

## Features

- Fluid multi-directional movement with AABB collision, wall sliding, and corner correction
- A bestiary of enemies with distinct behaviours (ranged casters, jumpers, player-mirroring shadows) and multi-phase bosses driven by state machines
- Combat system with several weapons (sword, spear, boomerang, bombs, fireball) and knockback / stun / invulnerability mechanics
- Interactive objects: chests, locked doors, crystal switches, NPCs with conditional dialogue, save points
- Animated room transitions, per-room music, and a full HUD (health, inventory)
- Save / load system with progression flags, serialized to JSON
- Screen management for title, pause, inventory, settings, save-select and game-over screens

---

## Technical overview

### Architecture

The codebase is organized as a modular package. The core is an `Entity` base class (position, stats, hitbox, combat mechanics) that everything inherits from — `Player`, `Enemy` (and its bosses), `AttackEntity`, and `Interactable` subclasses. A `GameScene` owns the game loop and delegates to focused managers (`TransitionManager`, `MusicManager`, `SaveManager`, `DialogueManager`), while a `ScreenManager` routes input and orchestrates application state.

Design patterns used where they earn their place:

- **State** — room transitions, application screens, and boss attack patterns
- **Registry** — enemies auto-register from their module and are instantiated directly from room JSON
- **Composite** — the scene treats entities, interactables, and attacks uniformly through a shared `update(dt, scene)` method

### Pathfinding

The `pathfinder` module is the algorithmic heart of the enemy AI:

- `get_walkable_grid()` converts room JSON into a boolean grid
- `flood_fill()` (recursive DFS) checks connectivity before committing to a search
- `astar()` runs A* with a priority queue and a Euclidean heuristic
- `line_of_sight()` raycasts to skip pathfinding when a straight path exists
- path smoothing removes redundant waypoints, and entity-size awareness keeps large enemies out of narrow gaps

---

## Getting started

> Requirements below are inferred from the project — verify against your environment and add a `requirements.txt` to make this reproducible.

```bash
# Clone
git clone https://github.com/Thr1lleX/Emby-s-Quest.git
cd Emby-s-Quest

# (recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install PyQt5 pygame

# Run
python main.py
```


## Testing

```bash
pytest tests/ -v
```

The suite covers the pathfinder (A*, grid construction, flood fill), the inventory, the save manager, and settings. A separate benchmark measures A* performance across open and obstacle-dense grids:

```bash
python tests/benchmark_astar.py
```

---

## Project structure

```
game/                core code (entities, scene, screens)
game/enemies/        bestiary
game/attacks/        weapons and projectiles
game/screens/        overlayable screens
game/interactables/  chests, doors, NPCs, switches
game/ui/             reusable UI components
assets/              sprites, tiles, HUD (by biome)
rooms/               JSON room definitions
tests/               unit tests and benchmarks
main.py              entry point
```

---

## Contributors

Built by two people:

- **Matéo Baldo** — core engine foundation, low-level physics, and the initial entity and save system, sound design, dialogue...
- **Ryan Collot** — enemy pathfinding (A*, flood fill, line-of-sight, path smoothing), the screen-management architecture and screen back-end, the items and effects systems...


---

## Acknowledgments

Inspired by the top-down *Zelda* formula. Built as a learning project to understand game architecture, real-time loops, and pathfinding from first principles — using PyQt5 as a deliberate constraint rather than a game-specific engine.
