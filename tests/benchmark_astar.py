# -*- coding: utf-8 -*-
"""
Benchmark A* — compare les performances avec et sans verification
de connexite (are_connected / flood_fill) avant l'appel A*.

Scenarios :
  1. Grille ouverte (chemin existe)           -> are_connected n'apporte rien
  2. Grille avec 25% d'obstacles (chemin ?)   -> cas mixte
  3. Mur vertical complet (chemin impossible)  -> are_connected evite un A* inutile
  4. Enclos ferme (chemin impossible)          -> idem, pire cas A*
"""
import sys, os, time, random, statistics, unittest.mock as mock
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({"font.size": 8})

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
for m in ("PyQt5","PyQt5.QtCore","PyQt5.QtGui","PyQt5.QtWidgets","PyQt5.QtMultimedia"):
    sys.modules.setdefault(m, mock.MagicMock())

from game.pathfinder import astar, are_connected, get_walkable_grid, flood_fill
from game.config import HUD_HEIGHT

# ───────────────────────────────────────
# Parametres
# ───────────────────────────────────────
TILE, ROWS, COLS, N = 32, 11, 16, 200
OUT = os.path.join(os.path.dirname(__file__), "benchmark_astar.png")

def px(col, row):
    return (col * TILE + TILE / 2, (row + HUD_HEIGHT) * TILE + TILE / 2)

# ───────────────────────────────────────
# Grilles de test
# ───────────────────────────────────────
def open_grid():
    return [[True] * COLS for _ in range(ROWS)]

def obstacle_grid(ratio=0.25):
    random.seed(42)
    g = [[random.random() >= ratio for _ in range(COLS)] for _ in range(ROWS)]
    g[1][1] = g[ROWS - 2][COLS - 2] = True
    return g

def wall_grid():
    """Mur vertical complet en colonne 8 — deux zones deconnectees."""
    g = open_grid()
    for r in range(ROWS):
        g[r][8] = False
    return g

def enclosure_grid():
    """Depart enferme dans un enclos 3x3 — pire cas pour A*."""
    g = open_grid()
    # murs autour de (1,1) : cases (0..2, 0..2) fermees sauf (1,1)
    for r in range(0, 4):
        g[r][3] = False     # mur droit
    for c in range(0, 4):
        g[3][c] = False     # mur bas
    return g

# ───────────────────────────────────────
# Scenarios : (nom, grille, start, goal)
# ───────────────────────────────────────
SCENARIOS = [
    ("Ouverte (0%)",       open_grid,      px(1, 1), px(COLS - 2, ROWS - 2)),
    ("Obstacles (25%)",    obstacle_grid,  px(1, 1), px(COLS - 2, ROWS - 2)),
    ("Mur vertical",       wall_grid,      px(1, 1), px(COLS - 2, ROWS - 2)),
    ("Enclos ferme",       enclosure_grid, px(1, 1), px(COLS - 2, ROWS - 2)),
]

# ───────────────────────────────────────
# Strategies a comparer
# ───────────────────────────────────────
def strategy_astar_only(grid, start, goal):
    """A* brut, sans pre-verification."""
    return astar(grid, start, goal, TILE, 1, 1)

def strategy_connected_then_astar(grid, start, goal):
    """Verifie la connexite d'abord ; A* seulement si connecte."""
    if not are_connected(grid, start, goal, TILE):
        return None
    return astar(grid, start, goal, TILE, 1, 1)

STRATEGIES = {
    "A* seul":                 strategy_astar_only,
    "are_connected + A*":      strategy_connected_then_astar,
}

# ───────────────────────────────────────
# Mesures
# ───────────────────────────────────────
# results[strategy_name][scenario_name] = list[float]  (ms)
results = {s: {} for s in STRATEGIES}

for sc_name, grid_fn, start, goal in SCENARIOS:
    grid = grid_fn()
    for strat_name, strat_fn in STRATEGIES.items():
        times = []
        for _ in range(N):
            t0 = time.perf_counter()
            strat_fn(grid, start, goal)
            times.append((time.perf_counter() - t0) * 1000)
        results[strat_name][sc_name] = times

# ───────────────────────────────────────
# Affichage console
# ───────────────────────────────────────
print(f"\n{'Strategie':<25} {'Scenario':<20} {'Moy':>8} {'Med':>8} {'Min':>8} {'Max':>8}")
print("-" * 85)
for strat_name in STRATEGIES:
    for sc_name in [s[0] for s in SCENARIOS]:
        t = results[strat_name][sc_name]
        print(f"{strat_name:<25} {sc_name:<20} {statistics.mean(t):>7.3f}ms"
              f" {statistics.median(t):>7.3f}ms {min(t):>7.3f}ms {max(t):>7.3f}ms")
    print()

FRAME_MS = 16
print(f"Budget frame @60fps : {FRAME_MS} ms\n")

# ───────────────────────────────────────
# Visualisation matplotlib (6 panneaux)
# ───────────────────────────────────────
scenario_names = [s[0] for s in SCENARIOS]
strat_names = list(STRATEGIES.keys())
colors_strat = {"A* seul": "#4C9BE8", "are_connected + A*": "#2ECC71"}

fig = plt.figure(figsize=(16, 10))
fig.suptitle(f"Benchmark A*  —  {N} appels par scenario\n"
             "Comparaison : A* seul  vs  are_connected + A*",
             fontweight="bold", fontsize=12)

gs = fig.add_gridspec(2, 3, hspace=0.4, wspace=0.35)

# ── Panneau 1 : Histogramme superpose par scenario (chemins possibles) ──
ax1 = fig.add_subplot(gs[0, 0])
for sc in scenario_names[:2]:  # ouverte + obstacles
    for sn in strat_names:
        ax1.hist(results[sn][sc], bins=25, alpha=0.45,
                 label=f"{sn} – {sc.split()[0]}",
                 color=colors_strat[sn])
ax1.axvline(FRAME_MS, color="red", ls="--", lw=1.3, label=f"Budget frame ({FRAME_MS} ms)")
ax1.set_xlabel("Duree par appel (ms)")
ax1.set_ylabel("Nombre d'appels")
ax1.set_title("Chemin POSSIBLE")
ax1.legend(fontsize=6)
ax1.grid(linestyle = "--", zorder = 0)

# ── Panneau 2 : Histogramme superpose (chemins impossibles) ──
ax2 = fig.add_subplot(gs[0, 1])
for sc in scenario_names[2:]:  # mur + enclos
    for sn in strat_names:
        ax2.hist(results[sn][sc], bins=25, alpha=0.45,
                 label=f"{sn} – {sc.split()[0]}",
                 color=colors_strat[sn])
ax2.axvline(FRAME_MS, color="red", ls="--", lw=1.3, label=f"Budget frame")
ax2.set_xlabel("Duree par appel (ms)")
ax2.set_title("Chemin IMPOSSIBLE")
ax2.legend(fontsize=6)
ax2.grid(linestyle = "--", zorder = 0)

# ── Panneau 3 : Barplot comparatif des moyennes ──
ax3 = fig.add_subplot(gs[0, 2])
x = range(len(scenario_names))
bar_w = 0.35
for i, sn in enumerate(strat_names):
    means = [statistics.mean(results[sn][sc]) for sc in scenario_names]
    bars = ax3.bar([xi + i * bar_w for xi in x], means, bar_w,
                   label=sn, color=colors_strat[sn], alpha=0.85, zorder = 67)
    for bar, val in zip(bars, means):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                 f"{val:.3f}", ha="center", va="bottom", fontsize=6)
ax3.set_xticks([xi + bar_w / 2 for xi in x])
ax3.set_xticklabels([s.split("(")[0].strip() for s in scenario_names], fontsize=7)
ax3.set_ylabel("Duree moyenne (ms)")
ax3.set_title("Comparaison des moyennes")
ax3.legend(fontsize=7)
ax3.grid(linestyle = "--", zorder = 0)

# ── Panneau 4 : Boxplot par scenario ──
ax4 = fig.add_subplot(gs[1, 0])
box_data = []
box_labels = []
box_colors = []
for sc in scenario_names:
    for sn in strat_names:
        box_data.append(results[sn][sc])
        box_labels.append(f"{sc.split()[0]}\n{sn.split()[0]}")
        box_colors.append(colors_strat[sn])

bp = ax4.boxplot(box_data, labels=box_labels, patch_artist=True,
                 medianprops=dict(color="white", linewidth=1.5))
for patch, c in zip(bp["boxes"], box_colors):
    patch.set_facecolor(c)
    patch.set_alpha(0.7)
# ax4.axhline(FRAME_MS, color="red", ls="--", lw=1)
ax4.set_ylabel("Duree (ms)")
ax4.set_title("Boxplot comparatif")
ax4.tick_params(axis="x", labelsize=5.5)
ax4.grid(linestyle = "--", zorder = 0)

# ── Panneau 5 : Speedup (ratio A* seul / are_connected+A*) ──
ax5 = fig.add_subplot(gs[1, 1])
speedups = []
for sc in scenario_names:
    mean_alone = statistics.mean(results["A* seul"][sc])
    mean_conn  = statistics.mean(results["are_connected + A*"][sc])
    speedups.append(mean_alone / mean_conn if mean_conn > 0 else 1.0)

bar_colors = ["#E86B4C" if s > 1.05 else "#95A5A6" if s >= 0.95 else "#4C9BE8"
              for s in speedups]
bars = ax5.bar(range(len(scenario_names)), speedups, color=bar_colors, alpha=0.85, zorder = 67)
ax5.axhline(1.0, color="gray", ls="--", lw=1, label="x1 (egalite)")
for bar, val in zip(bars, speedups):
    ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
             f"x{val:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
ax5.set_xticks(range(len(scenario_names)))
ax5.set_xticklabels([s.split("(")[0].strip() for s in scenario_names], fontsize=7)
ax5.set_ylabel("Speedup (A* seul / connected+A*)")
ax5.set_title("Gain de performance")
ax5.legend(fontsize=7)
ax5.grid(linestyle = "--", zorder = 0)


# ── Panneau 6 : Tableau recapitulatif ──
ax6 = fig.add_subplot(gs[1, 2])
ax6.axis("off")
col_labels = [s.split("(")[0].strip() for s in scenario_names]
row_labels = ["A* seul (ms)", "connected+A* (ms)", "Speedup", "% frame (A*)", "% frame (c+A*)"]
cells = []
cells.append([f"{statistics.mean(results['A* seul'][sc]):.3f}" for sc in scenario_names])
cells.append([f"{statistics.mean(results['are_connected + A*'][sc]):.3f}" for sc in scenario_names])
cells.append([f"x{s:.2f}" for s in speedups])
cells.append([f"{statistics.mean(results['A* seul'][sc]) / FRAME_MS * 100:.1f}%"
              for sc in scenario_names])
cells.append([f"{statistics.mean(results['are_connected + A*'][sc]) / FRAME_MS * 100:.1f}%"
              for sc in scenario_names])

tbl = ax6.table(cellText=cells, rowLabels=row_labels, colLabels=col_labels,
                cellLoc="center", loc="center")
tbl.auto_set_font_size(False)
tbl.set_fontsize(7)
tbl.scale(1.1, 1.6)

# Coloriser les cellules speedup
for j in range(len(scenario_names)):
    cell = tbl[3, j]  # ligne speedup (index 3 car header = 0)
    if speedups[j] > 1.05:
        cell.set_facecolor("#D5F5E3")
    elif speedups[j] < 0.95:
        cell.set_facecolor("#FADBD8")

ax6.set_title("Recapitulatif", pad=14)

plt.savefig(OUT, dpi=140, bbox_inches="tight")
print(f"\nGraphique sauvegarde : {OUT}")
