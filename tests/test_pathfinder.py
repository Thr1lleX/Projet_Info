# -*- coding: utf-8 -*-
import sys, os, math, unittest, unittest.mock as mock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
for m in ("PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.QtMultimedia"):
    sys.modules.setdefault(m, mock.MagicMock())

from game.pathfinder import heuristic, get_walkable_grid, astar, smooth_path
from game.config import HUD_HEIGHT

TILE = 32
ROWS, COLS = 11, 16

def open_grid(): return [[True]*COLS for _ in range(ROWS)]
def px(col, row): return (col*TILE + TILE/2, (row+HUD_HEIGHT)*TILE + TILE/2)

class TestPathfinder(unittest.TestCase):

    # heuristiques
    def test_heuristic_zero(self):
        self.assertAlmostEqual(heuristic((3,4),(3,4)), 0.0)

    def test_heuristic_345(self):
        self.assertAlmostEqual(heuristic((0,0),(3,4)), 5.0)

    def test_heuristic_symmetric(self):
        self.assertAlmostEqual(heuristic((2,7),(5,3)), heuristic((5,3),(2,7)))

    # get_walkable_grid
    def test_floor_walkable(self):
        grid = get_walkable_grid({"tiles": [[0,0],[0,0]]})
        self.assertTrue(all(c for row in grid for c in row))

    def test_wall_not_walkable(self):
        grid = get_walkable_grid({"tiles": [[2,0]]})
        self.assertFalse(grid[0][0])
        self.assertTrue(grid[0][1])

    #  astar 
    def test_path_found(self):
        path = astar(open_grid(), px(1,1), px(COLS-2, ROWS-2), TILE, 1, 1)
        self.assertIsNotNone(path)
        self.assertGreater(len(path), 0)

    def test_no_path_blocked_grid(self):
        blocked = [[False]*COLS for _ in range(ROWS)]
        path = astar(blocked, px(1,1), px(14,9), TILE, 1, 1)
        self.assertIsNone(path)

    def test_start_equals_goal(self):
        pos  = px(5,5)
        path = astar(open_grid(), pos, pos, TILE, 1, 1)
        self.assertTrue(path is None or len(path) == 0)

    #  smooth_path 
    def test_short_path_unchanged(self):
        pts = [px(0,0), px(5,5)]
        self.assertEqual(smooth_path(pts, open_grid(), TILE, 1, 1), pts)

    def test_empty_path(self):
        self.assertEqual(smooth_path([], open_grid(), TILE, 1, 1), [])

    def test_collinear_simplified(self):
        pts = [px(c,3) for c in range(1,6)]
        res = smooth_path(pts, open_grid(), TILE, 1, 1)
        self.assertLessEqual(len(res), len(pts))

if __name__ == "__main__":
    unittest.main()
