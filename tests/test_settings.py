# -*- coding: utf-8 -*-
import sys, os, json, tempfile, unittest, unittest.mock as mock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
for m in ("PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.QtMultimedia"):
    sys.modules.setdefault(m, mock.MagicMock())

from game.config import BASE_TILE_SIZE, BASE_SPEED_pxl
from game.settings import Settings

class TestSettings(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg = os.path.join(self.tmp, "s.json")

    def make(self, data=None):
        if data:
            with open(self.cfg, "w") as f: json.dump(data, f)
        return Settings(filepath=self.cfg)

    #  tile_size 
    def test_tile_size_scale1(self):
        s = self.make({"scale": 1.0})
        self.assertAlmostEqual(s.tile_size, BASE_TILE_SIZE * 1.0)

    def test_tile_size_scale3(self):
        s = self.make({"scale": 3.0})
        self.assertAlmostEqual(s.tile_size, BASE_TILE_SIZE * 3.0)

    #  base_speed   
    def test_base_speed_scale1(self):
        s = self.make({"scale": 1.0})
        self.assertAlmostEqual(s.base_speed, BASE_SPEED_pxl)

    def test_base_speed_scale3(self):
        s = self.make({"scale": 3.0})
        self.assertAlmostEqual(s.base_speed, BASE_SPEED_pxl * 3.0)

    #  load 
    def test_load_values(self):
        s = self.make({"scale": 2.0, "control_scheme": "azerty", "crt_overlay": False})
        self.assertAlmostEqual(s.scale, 2.0)
        self.assertEqual(s.control_scheme, "azerty")
        self.assertFalse(s.crt_overlay)

    def test_load_missing_file_defaults(self):
        s = Settings(filepath=os.path.join(self.tmp, "nope.json"))
        self.assertAlmostEqual(s.scale, 3.0)  # valeur par défaut

    # --- save ---
    def test_save_writes_values(self):
        s = self.make({"scale": 2.0})
        s.scale = 1.5; s.save()
        with open(self.cfg) as f: data = json.load(f)
        self.assertAlmostEqual(data["scale"], 1.5)

    def test_save_reload_roundtrip(self):
        s = self.make()
        s.scale = 2.5; s.save()
        s2 = Settings(filepath=self.cfg)
        self.assertAlmostEqual(s2.tile_size, BASE_TILE_SIZE * 2.5)

if __name__ == "__main__":
    unittest.main()
