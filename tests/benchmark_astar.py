# -*- coding: utf-8 -*-
import sys, os, time, random, statistics, unittest.mock as mock, matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
for m in ("PyQt5","PyQt5.QtCore","PyQt5.QtGui","PyQt5.QtWidgets","PyQt5.QtMultimedia"):
    sys.modules.setdefault(m, mock.MagicMock())

from game.pathfinder import astar
from game.config import HUD_HEIGHT

# Parametres
TILE, ROWS, COLS, N = 32, 11, 16, 200
OUT = os.path.join(os.path.dirname(__file__), "benchmark_astar.png")

def px(col, row):
    return (col*TILE + TILE/2, (row+HUD_HEIGHT)*TILE + TILE/2)

def open_grid():
    return [[True]*COLS for _ in range(ROWS)]

def obstacle_grid(ratio=0.25):
    random.seed(42)
    g = [[random.random() >= ratio]*COLS for _ in range(ROWS)] # True si libre
    g[1][1] = g[ROWS-2][COLS-2] = True
    return g

SCENARIOS = {
    "Ouverte (0%)":   (open_grid,     px(1,1), px(COLS-2, ROWS-2)),
    "Obstacles (25%)":(obstacle_grid, px(1,1), px(COLS-2, ROWS-2)),
}

# mesure
results = {}
for name, (grid_fn, start, goal) in SCENARIOS.items():
    grid = grid_fn()
    times = []
    for _ in range(N):
        t0 = time.perf_counter()
        astar(grid, start, goal, TILE, 1, 1)
        times.append((time.perf_counter() - t0) * 1000)
    results[name] = times


print(f"\n{'Scénario':<20} {'Total':>9} {'Moy':>8} {'Med':>8} {'Min':>8} {'Max':>8}")
print("-" * 65)
for name, times in results.items():
    print(f"{name:<20} {sum(times):>8.1f}ms {statistics.mean(times):>7.3f}ms"
          f" {statistics.median(times):>7.3f}ms {min(times):>7.3f}ms {max(times):>7.3f}ms")

# budget fps
print(f"\nBudget frame @60fps : 16.7 ms")
for name, times in results.items():
    pct = statistics.mean(times) / 16.7 * 100
    print(f"  {name}: {statistics.mean(times):.3f} ms/appel -> {pct:.1f}% du budget frame")


FRAME_MS = 16.7  # budget 60fps


fig = plt.figure(figsize=(13, 5))
fig.suptitle(f"Benchmark A*  —  {N} appels par scénario", fontweight="bold")
gs = fig.add_gridspec(1, 3, width_ratios=[2, 1.5, 1.5], wspace=0.35)
ax1, ax2, ax3 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
colors = ["#4C9BE8", "#E86B4C"]
for (name, times), color in zip(results.items(), colors):
    ax1.hist(times, bins=30, alpha=0.7, label=name, color=color)
ax1.axvline(FRAME_MS, color="red",    linestyle="--", linewidth=1.5, label=f"Budget frame ({FRAME_MS} ms)")
ax1.axvline(FRAME_MS/4, color="orange", linestyle=":", linewidth=1.2, label=f"25% budget ({FRAME_MS/4:.1f} ms)")
ax1.set_xlabel("Durée par appel (ms)")
ax1.set_ylabel("Nombre d'appels")
ax1.set_title("Distribution des temps")
ax1.legend(fontsize=7)

    # --- Boxplot coloré ---
bp = ax2.boxplot(list(results.values()), labels=[n.split()[0] for n in results],
                     patch_artist=True, medianprops=dict(color="white", linewidth=2))
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color); patch.set_alpha(0.8)
ax2.axhline(FRAME_MS,   color="red",    linestyle="--", linewidth=1.2)
ax2.axhline(FRAME_MS/4, color="orange", linestyle=":",  linewidth=1.0)
ax2.set_ylabel("Durée par appel (ms)")
ax2.set_title("Boxplot comparatif")

    # --- Tableau récapitulatif ---
ax3.axis("off")
rows  = ["Total (ms)", "Moy (ms)", "Med (ms)", "Min (ms)", "Max (ms)", "% frame"]
cols  = [n.split()[0] for n in results]
cells = []
for row_i, fn in enumerate([sum, statistics.mean, statistics.median, min, max]):
    cells.append([f"{fn(t):.3f}" for t in results.values()])
cells.append([f"{statistics.mean(t)/FRAME_MS*100:.1f}%" for t in results.values()])
tbl = ax3.table(cellText=cells, rowLabels=rows, colLabels=cols,
cellLoc="center", loc="center")
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1, 1.5)
ax3.set_title("Statistiques", pad=12)

plt.savefig(OUT, dpi=120, bbox_inches="tight")
print(f"\nGraphique : {OUT}")
